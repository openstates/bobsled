import datetime
import boto3
from botocore.exceptions import ClientError
from ..base import RunService, Status


class ECSRunService(RunService):
    def __init__(
        self, persister, cluster_name, subnet_id, security_group_id, log_group
    ):
        self.persister = persister
        self.cluster_name = cluster_name
        self.subnet_id = subnet_id
        self.security_group_id = security_group_id
        self.log_group = log_group
        self.ecs = boto3.client("ecs")

    def initialize(self, tasks):
        for task in tasks:
            self.register_task(task)

    def register_task(self, task):
        region = self.ecs.meta.region_name
        log_stream_prefix = task.name.lower()

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
            "environment": [],
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
            account_id = boto3.client("sts").get_caller_identity().get("Account")
            # TODO: create this role?
            role_arn = "arn:aws:iam::{}:role/{}".format(
                account_id, "ecs-fargate-bobsled"
            )
            print(task.cpu, task.memory)
            response = self.ecs.register_task_definition(
                family=task.name,
                containerDefinitions=[main_container],
                cpu=str(task.cpu),
                memory=str(task.memory),
                networkMode="awsvpc",
                executionRoleArn=role_arn,
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
                print("missing")
                return
            # can be MISSING or ??? (TODO: handle)
            raise ValueError(f"unexpected status: {resp['failures']}")

        result = resp["tasks"][0]
        if result["lastStatus"] == "STOPPED":
            run.exit_code = result["containers"][0]["exitCode"]
            # TODO: handle cases where we need to use containers[0][reason]
            run.end = datetime.datetime.utcnow().isoformat()
            run.status = Status.Error if run.exit_code else Status.Success
            run.logs = self.get_logs(run)
            await self.persister.save_run(run)

        elif (
            run.run_info["timeout_at"]
            and datetime.datetime.utcnow().isoformat() > run.run_info["timeout_at"]
        ):
            run.logs = self.get_logs(run)
            self.stop(run)
            run.status = Status.TimedOut
            await self.persister.save_run(run)

        elif result["lastStatus"] == "RUNNING":
            if update_logs:
                run.logs = self.get_logs(run)
            if run.status != Status.Running or update_logs:
                run.status = Status.Running
                await self.persister.save_run(run)
        elif result["lastStatus"] in ("PENDING", "PROVISIONING"):
            if run.status != Status.Pending:
                run.status = Status.Pending
                await self.persister.save_run(run)

        return run

    def stop(self, run):
        self.ecs.stop_task(cluster=self.cluster_name, task=run.run_info["task_arn"])

    def get_logs(self, run):
        return "\n".join(l["message"] for l in self.iter_logs(run))

    def iter_logs(self, run):
        logs = boto3.client("logs")
        arn_uuid = run.run_info["task_arn"].split("/")[-1]
        log_arn = f"{run.task}/{run.task}/{arn_uuid}"

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
