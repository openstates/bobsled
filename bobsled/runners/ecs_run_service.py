import datetime
import boto3
from botocore.exceptions import ClientError
from ..base import RunService, Status


class ECSRunService(RunService):
    def __init__(
        self,
        persister,
        environment,
        callbacks=None,
        *,
        cluster_name,
        subnet_id,
        security_group_id,
        log_group,
        role_arn,
    ):
        self.persister = persister
        self.environment = environment
        self.callbacks = callbacks or []
        self.cluster_name = cluster_name
        self.subnet_id = subnet_id
        self.security_group_id = security_group_id
        self.log_group = log_group
        self.role_arn = role_arn
        self.ecs = boto3.client("ecs")

        self.cluster_arn = self.ecs.describe_clusters(clusters=[self.cluster_name])[
            "clusters"
        ][0]["clusterArn"]

    def initialize(self, tasks):
        for task in tasks:
            self._register_task(task)
            # self._make_cron_rule(task)

    def _register_task(self, task):
        region = self.ecs.meta.region_name
        log_stream_prefix = task.name.lower()

        env_list = []
        if task.environment:
            env = self.environment.get_environment(task.environment)
            env_list = [{"name": k, "value": v} for k, v in env.values.items()]

        main_container = {
            "name": task.name,
            "image": task.image,
            "essential": True,
            "entryPoint": task.entrypoint.split(),
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": self.log_group,
                    "awslogs-region": region,
                    "awslogs-stream-prefix": log_stream_prefix,
                },
            },
            "environment": env_list,
        }

        # add env to main_container
        create = False
        existing = None
        try:
            resp = self.ecs.describe_task_definition(taskDefinition=task.name)
            existing = resp["taskDefinition"]

            if str(task.memory) != existing["memory"]:
                print(
                    "{}: changing memory: {} => {}".format(
                        task.name, existing["memory"], task.memory
                    )
                )
                create = True
            if str(task.cpu) != existing["cpu"]:
                print(
                    "{}: changing cpu: {} => {}".format(
                        task.name, existing["cpu"], task.cpu
                    )
                )
                create = True

            for key in (
                "entryPoint",
                "environment",
                "image",
                "name",
                "essential",
                "logConfiguration",
            ):

                # check if values differ for this key
                oldval = existing["containerDefinitions"][0][key]
                newval = main_container[key]
                if key == "environment":
                    s_oldval = sorted([tuple(i.items()) for i in oldval])
                    s_newval = sorted([tuple(i.items()) for i in newval])
                    differ = s_oldval != s_newval
                else:
                    differ = oldval != newval

                if differ:
                    create = True
                    print(f"{task.name}: changing {key}: {oldval} => {newval}")
        except ClientError:
            create = True

        # if force and not create:
        #     print(f'{task.name}: forced update')
        #     create = True

        if create:
            response = self.ecs.register_task_definition(
                family=task.name,
                containerDefinitions=[main_container],
                cpu=str(task.cpu),
                memory=str(task.memory),
                networkMode="awsvpc",
                executionRoleArn=self.role_arn,
                requiresCompatibilities=["FARGATE"],
            )
            return response
        elif existing:
            pass
            # print(f'{task.name}: definition matches {task.name}:{existing["revision"]}')
        else:
            print(f"{task.name}: creating new task")

    def start_task(self, task):
        resp = self.ecs.run_task(
            cluster=self.cluster_name,
            count=1,
            taskDefinition=task.name,
            startedBy="bobsled",
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [self.subnet_id],
                    "securityGroups": [self.security_group_id],
                    "assignPublicIp": "ENABLED",
                }
            },
        )
        return {"task_arn": resp["tasks"][0]["taskArn"]}

    async def update_status(self, run_id, update_logs=False):
        run = await self.persister.get_run(run_id)

        if run.status.is_terminal():
            return run

        # note: what ECS calls a task, we call a run
        arn = run.run_info["task_arn"]
        resp = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=[arn])

        if resp["failures"]:
            if resp["failures"][0]["reason"] == "MISSING":
                run.exit_code = -999
                run.end = datetime.datetime.utcnow().isoformat()
                run.status = Status.Error
                run.logs = self.get_logs(run)
                await self.persister.save_run(run)
                return run
                # TODO: improve handling, should we call callbacks on missing?
            raise ValueError(f"unexpected status: {resp['failures']}")

        result = resp["tasks"][0]
        if result["lastStatus"] == "STOPPED":
            run.exit_code = result["containers"][0]["exitCode"]
            # TODO: handle cases where we need to use containers[0][reason]
            run.end = datetime.datetime.utcnow().isoformat()
            run.status = Status.Error if run.exit_code else Status.Success
            run.logs = self.get_logs(run)
            await self.persister.save_run(run)
            await self.trigger_callbacks(run)

        elif (
            run.run_info["timeout_at"]
            and datetime.datetime.utcnow().isoformat() > run.run_info["timeout_at"]
        ):
            run.logs = self.get_logs(run)
            self.stop(run)
            run.status = Status.TimedOut
            await self.persister.save_run(run)
            await self.trigger_callbacks(run)

        elif result["lastStatus"] == "RUNNING":
            if run.status != Status.Running:
                run.status = Status.Running
                run.logs = self.get_logs(run)
                await self.persister.save_run(run)
                await self.trigger_callbacks(run)
            elif update_logs:
                run.logs = self.get_logs(run)
                await self.persister.save_run(run)
        elif result["lastStatus"] in ("PENDING", "PROVISIONING"):
            if run.status != Status.Pending:
                run.status = Status.Pending
                await self.persister.save_run(run)
                await self.trigger_callbacks(run)

        return run

    def stop(self, run):
        self.ecs.stop_task(cluster=self.cluster_name, task=run.run_info["task_arn"])

    def get_logs(self, run):
        return self.environment.mask_variables(
            "\n".join(l["message"] for l in self.iter_logs(run))
        )

    def iter_logs(self, run):
        logs = boto3.client("logs")
        arn_uuid = run.run_info["task_arn"].split("/")[-1]
        log_arn = f"{run.task.lower()}/{run.task}/{arn_uuid}"

        next_token = None

        while True:
            extra = {"nextToken": next_token} if next_token else {}
            try:
                events = logs.get_log_events(
                    logGroupName=self.log_group, logStreamName=log_arn, **extra
                )
            except ClientError:
                yield {"message": "no logs"}
                break
            next_token = events["nextForwardToken"]

            if not events["events"]:
                break

            yield from events["events"]

            if not next_token:
                break

    async def cleanup(self):
        n = 0
        for r in await self.persister.get_runs(status=[Status.Pending, Status.Running]):
            self.ecs.stop_task(cluster=self.cluster_name, task=r.run_info["task_arn"])
            n += 1
        return n

    def _make_cron_rule(self, task):
        """
        registers a cron rule with ECS

        currently inactive code since ECS scheduling doesn't have a clean way to
        add a run entry in the run persister.
        """
        events = boto3.client("events")

        schedule = None
        for trigger in task.triggers:
            if trigger["cron"]:
                schedule = (
                    f"cron({trigger['cron']} *)"  # ECS cron requires year, add a *
                )
                break
        if not schedule:
            return

        resp = self.ecs.describe_task_definition(taskDefinition=task.name)
        task_def_arn = resp["taskDefinition"]["taskDefinitionArn"]

        enabled = "ENABLED" if task.enabled else "DISABLED"
        create = False

        try:
            old_rule = events.describe_rule(Name=task.name)
            updating = []
            if schedule != old_rule["ScheduleExpression"]:
                updating.append("schedule")
            if enabled != old_rule["State"]:
                updating.append("enabled")
            if updating:
                create = True
        except ClientError:
            create = True

        if create:
            events.put_rule(
                Name=task.name,
                ScheduleExpression=schedule,
                State=enabled,
                Description=f"run {task.name} at {schedule}",
            )
            events.put_targets(
                Rule=task.name,
                Targets=[
                    {
                        "Id": "run-target",
                        "Arn": self.cluster_arn,
                        "RoleArn": self.role_arn,
                        "EcsParameters": {
                            "TaskDefinitionArn": task_def_arn,
                            "TaskCount": 1,
                            "LaunchType": "FARGATE",
                            "NetworkConfiguration": {
                                "awsvpcConfiguration": {
                                    "Subnets": [self.subnet_id],
                                    "SecurityGroups": [self.security_group_id],
                                    "AssignPublicIp": "ENABLED",
                                }
                            },
                        },
                    }
                ],
            )
