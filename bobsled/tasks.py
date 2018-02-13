import os
import glob
import json
from functools import lru_cache
import yaml
import boto3
from botocore.exceptions import ClientError

from .dynamo import Run
from . import config


def checkout_tasks():
    os.system('GIT_SSH_COMMAND="ssh -i deploy.key" '
              'git clone git@github.com:{}/{}.git --depth 1'.format(
                  config.GITHUB_USER, config.GITHUB_TASK_REPO
              ))


def get_all_ssm_parameters(path):
    ssm = boto3.client('ssm')
    resp = ssm.get_parameters_by_path(Path=path, WithDecryption=True)
    yield from resp['Parameters']

    while True:
        try:
            next_token = resp['NextToken']
        except KeyError:
            break

        resp = ssm.get_parameters_by_path(Path=path, WithDecryption=True, NextToken=next_token)
        yield from resp['Parameters']


@lru_cache()
def get_env(name):
    env = {}
    prefix = '/bobsled/{}/'.format(name)
    for param in get_all_ssm_parameters(prefix):
        key = param['Name']
        value = param['Value']
        env[key.replace(prefix, '')] = value
    return env


def load_tasks(directory):
    environments = yaml.load(open(os.path.join(directory, 'environments.yaml')))

    tasks = []

    files = glob.glob(os.path.join(directory, 'tasks/*.yml'))
    for fn in files:
        with open(fn) as f:
            task = yaml.load(f)
            # environment can be a string and will be looked up in environments
            # or can be a dict and will be used as-is
            if isinstance(task['environment'], str):
                task['environment'] = environments[task['environment']]

            if task.get('paramstore', None):
                task['environment'].update(get_env(task['paramstore']))
            tasks.append(task)

    return tasks


def make_task(family,
              entrypoint,
              image,
              memory_soft=128,
              environment=None,
              verbose=False,
              force=False,
              cpu='256',
              memory='512',
              ):
    ecs = boto3.client('ecs')
    region = ecs.meta.region_name

    log_stream_prefix = family.lower()
    main_container = {
        'name': config.TASK_NAME,
        'image': image,
        'essential': True,
        'entryPoint': entrypoint,
        'memoryReservation': memory_soft,
        'logConfiguration': {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": config.LOG_GROUP,
                "awslogs-region": region,
                "awslogs-stream-prefix": log_stream_prefix
            }
        },
    }

    if environment:
        main_container['environment'] = [{'name': k, 'value': v}
                                         for k, v in environment.items()]

    create = False
    existing = None
    try:
        resp = ecs.describe_task_definition(taskDefinition=family)
        existing = resp['taskDefinition']

        if memory != existing['memory']:
            print('{}: changing memory: {} => {}'.format(family, existing['memory'], memory))
            create = True
        if cpu != existing['cpu']:
            print('{}: changing cpu: {} => {}'.format(family, existing['cpu'], cpu))
            create = True

        for key in ('entryPoint', 'environment', 'image', 'name',
                    'memoryReservation', 'essential', 'logConfiguration'):

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
                print('{}: changing {}: {} => {}'.format(family, key, oldval, newval))
    except ClientError:
        create = True

    if force and not create:
        print('{}: forced update'.format(family))
        create = True

    if create:
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        # TODO: create this role?
        role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, 'ecs-fargate-bobsled')
        response = ecs.register_task_definition(
            family=family,
            containerDefinitions=[
                main_container
            ],
            cpu=cpu,
            memory=memory,
            networkMode='awsvpc',
            executionRoleArn=role_arn,
            requiresCompatibilities=['EC2', 'FARGATE'],
        )
        return response
    elif existing:
        if verbose:
            print('{family}: definition matches {family}:{revision}'.format(**existing))
    else:
        print('{}: creating new task'.format(family))


def make_cron_rule(name, schedule, enabled, force=False, verbose=False):
    events = boto3.client('events')
    lamb = boto3.client('lambda')

    enabled = 'ENABLED' if enabled else 'DISABLED'
    create = False

    try:
        old_rule = events.describe_rule(Name=name)
        updating = []
        if schedule != old_rule['ScheduleExpression']:
            updating.append('schedule')
        if enabled != old_rule['State']:
            updating.append('enabled')
        if updating:
            print('{}: updating rule'.format(name), ' '.join(updating))
            create = True
    except ClientError:
        print('{}: creating new cron rule'.format(name), schedule)
        create = True

    if force:
        create = True

    # figure out full lambda arn
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = events.meta.region_name
    lambda_arn = 'arn:aws:lambda:{}:{}:function:bobsled-dev'.format(region, account_id)

    if create:
        rule = events.put_rule(
            Name=name,
            ScheduleExpression=schedule,
            State=enabled,
            Description='run {} at {}'.format(name, schedule),
        )
        events.put_targets(
            Rule=name,
            Targets=[
                {
                    'Id': name + '-job',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'job': name,
                        'command': 'bobsled.tasks.run_task_handler',
                    })
                }
            ]
        )
        perm_statement_id = name + '-job-permission'
        try:
            lamb.add_permission(
                FunctionName=lambda_arn,
                StatementId=perm_statement_id,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule['RuleArn'],
            )
        except ClientError as e:
            print(e)
            # don't recreate permission if it is already there
            pass
    elif verbose:
        print('{}: no schedule change'.format(name))


def publish_task_definitions(dirname, only=None, force=False, verbose=False):
    tasks = load_tasks(dirname)

    for task in tasks:
        # convert entrypoint to list, break on spaces if needed
        entrypoint = task['entrypoint']
        if not isinstance(entrypoint, list):
            entrypoint = entrypoint.split()

        # shortcut for only adding certain task definitions
        if only and task['name'] not in only:
            continue

        make_task(task['name'],
                  entrypoint,
                  image=task.get('image'),
                  memory_soft=task.get('memory_soft', 128),
                  environment=task.get('environment'),
                  force=force,
                  verbose=verbose,
                  memory=str(task.get('memory', '512')),
                  cpu=str(task.get('cpu', '256')),
                  )
        if task.get('cron'):
            make_cron_rule(task['name'],
                           'cron({})'.format(task['cron']),
                           task.get('enabled', True),
                           force=force,
                           verbose=verbose,
                           )


def run_task(task_name, started_by):
    ecs = boto3.client('ecs')

    print('running', task_name)

    taskdef = ecs.describe_task_definition(taskDefinition=task_name)

    response = ecs.run_task(
        cluster=config.CLUSTER_NAME,
        count=1,
        taskDefinition=task_name,
        startedBy=started_by,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [config.SUBNET_ID],
                'securityGroups': [config.SECURITY_GROUP_ID],
                'assignPublicIp': 'ENABLED',
            }
        },
        # overrides={
        #    'containerOverrides': [
        #        {
        #            'name': 'string',
        #            'command': [
        #                'string',
        #            ],
        #            'environment': [
        #                {
        #                    'name': 'string',
        #                    'value': 'string'
        #                },
        #            ]
        #        },
        #    ],
        # },
    )

    Run(task_name,
        task_definition=taskdef['taskDefinition'],
        task_arn=response['tasks'][0]['taskArn'],
        ).save()
    return response


def run_task_handler(event, context):
    print(event, context)
    run_task(event['job'], 'lambda')
