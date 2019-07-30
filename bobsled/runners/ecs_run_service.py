import boto3
from botocore.exceptions import ClientError
from ..base import RunService


class ECSRunService(RunService):
    def __init__(self, cluster_name, subnet_id, security_group_id, log_group):
        self.cluster_name = cluster_name
        self.subnet_id = subnet_id
        self.security_group_id = security_group_id
        self.log_group = log_group
        self.ecs = boto3.client("ecs")

    def register_task(self, task):
        region = self.ecs.meta.region_name
        log_stream_prefix = task.name.lower()

        main_container = {
            'name': task.name,
            'image': task.image,
            'essential': True,
            'entryPoint': task.entrypoint.split(),
            'logConfiguration': {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": self.log_group,
                    "awslogs-region": region,
                    "awslogs-stream-prefix": log_stream_prefix,
                }
            },
            'environment': [],
        }

        # add env to main_container
        create = False
        existing = None
        try:
            resp = self.ecs.describe_task_definition(taskDefinition=task.name)
            existing = resp['taskDefinition']

            if str(task.memory) != existing['memory']:
                print('{}: changing memory: {} => {}'.format(
                    task.name, existing['memory'], task.memory)
                      )
                create = True
            if str(task.cpu) != existing['cpu']:
                print('{}: changing cpu: {} => {}'.format(task.name, existing['cpu'], task.cpu))
                create = True

            for key in ('entryPoint', 'environment', 'image', 'name',
                        'essential', 'logConfiguration'):

                # check if values differ for this key
                oldval = existing['containerDefinitions'][0][key]
                newval = main_container[key]
                if key == 'environment':
                    s_oldval = sorted([tuple(i.items()) for i in oldval])
                    s_newval = sorted([tuple(i.items()) for i in newval])
                    differ = (s_oldval != s_newval)
                else:
                    differ = (oldval != newval)

                if differ:
                    create = True
                    print(f'{task.name}: changing {key}: {oldval} => {newval}')
        except ClientError:
            create = True

        # if force and not create:
        #     print(f'{task.name}: forced update')
        #     create = True

        if create:
            account_id = boto3.client('sts').get_caller_identity().get('Account')
            # TODO: create this role?
            role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, 'ecs-fargate-bobsled')
            print(task.cpu, task.memory)
            response = self.ecs.register_task_definition(
                family=task.name,
                containerDefinitions=[
                    main_container
                ],
                cpu=str(task.cpu),
                memory=str(task.memory),
                networkMode='awsvpc',
                executionRoleArn=role_arn,
                requiresCompatibilities=['FARGATE'],
            )
            return response
        elif existing:
            pass
            # print(f'{task.name}: definition matches {task.name}:{existing["revision"]}')
        else:
            print(f'{task.name}: creating new task')

    def start_task(self, task):
        resp = self.ecs.run_task(
            cluster=self.cluster_name,
            count=1,
            taskDefinition=task.name,
            startedBy="bobsled",
            launchType="FARGATE",
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [self.subnet_id],
                    'securityGroups': [self.security_group_id],
                    'assignPublicIp': 'ENABLED',
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
        task = self.ecs.describe_tasks(self.cluster_name, tasks=[arn])

        if resp["failures"]:
            # can be MISSING or ??? (TODO: handle)
            raise ValueError(f"unexpected status: {failure}")

        result = resp["tasks"][0]
        if result["lastStatus"] == "STOPPED":
            run.exit_code = result["containers"][0]["exitCode"]
            run.end = datetime.datetime.utcnow().isoformat()
            run.status = Status.Error if run.exit_code else Status.Success
            await self.persister.save_run(run)
        elif result["lastStatus"] == "RUNNING":
            if run.status != Status.Running:
                run.status = Status.Running
                await self.persister.save_run(run)
        elif result["lastStatus"] == "PENDING":
            if run.status != Status.Pending:
                run.status = Status.Pending
                await self.persister.save_run(run)
        return run

    def stop(self, run):
        self.ecs.stop_task(self.cluster_name, run.run_info["task_arn"])
