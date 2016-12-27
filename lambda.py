import boto3

ecs = boto3.client('ecs', region_name='us-east-1')

ECS_CLUSTER = 'openstates-scrapers'


def run_task(task_definition, started_by):
    response = ecs.run_task(
        cluster=ECS_CLUSTER,
        count=1,
        taskDefinition=task_definition,
        startedBy=started_by,
    )
    return response


def handler(event, context):
    run_task(event['job'], 'lambda')
