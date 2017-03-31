from __future__ import print_function
import os
import glob
import json
import yaml
import boto3
from botocore.exceptions import ClientError

from .dynamo import Run


def checkout_tasks():
    os.system('GIT_SSH_COMMAND="ssh -i deploy.key" '
              'git clone git@github.com:{}/{}.git --depth 1'.format(
                  os.environ['BOBSLED_GITHUB_USER'],
                  os.environ['BOBSLED_GITHUB_TASK_REPO']
              ))


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
            tasks.append(task)

    return tasks


def make_scraper_task(family,
                      entrypoint,
                      image,
                      memory_soft=128,
                      name='openstates-scraper',
                      environment=None,
                      verbose=False,
                      force=False,
                      # cpu=None,
                      # memory=None,
                      ):
    ecs = boto3.client('ecs', region_name='us-east-1')

    log_stream_prefix = family.lower()
    main_container = {
        'name': name,
        'image': image,
        'essential': True,
        'entryPoint': entrypoint,
        'memoryReservation': memory_soft,
        'logConfiguration': {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "openstates-scrapers",
                "awslogs-region": "us-east-1",
                "awslogs-stream-prefix": log_stream_prefix
            }
        },
    }

    # TODO: add CPU/memory limits

    if environment:
        main_container['environment'] = [{'name': k, 'value': v}
                                         for k, v in environment.items()]

    create = False
    existing = None
    try:
        resp = ecs.describe_task_definition(taskDefinition=family)
        existing = resp['taskDefinition']
        for key in ('entryPoint', 'environment', 'image', 'name',
                    'memoryReservation', 'essential', 'logConfiguration'):

            # check if values differ for this key
            oldval = existing['containerDefinitions'][0][key]
            newval = main_container[key]
            if key == 'environment':
                differ = (sorted(oldval) != sorted(newval))
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
        response = ecs.register_task_definition(
            family=family,
            containerDefinitions=[
                main_container
            ],
        )
        return response
    elif existing:
        if verbose:
            print('{family}: definition matches {family}:{revision}'.format(**existing))
    else:
        print('{}: creating new task'.format(family))


def make_cron_rule(name, schedule, enabled, force=False, verbose=False):
    events = boto3.client('events', region_name='us-east-1')
    lamb = boto3.client('lambda', region_name='us-east-1')

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
                    'Id': name + '-scrape',
                    'Arn': os.environ['BOBSLED_LAMBDA_ARN'],
                    'Input': json.dumps({'job': name})
                }
            ]
        )
        perm_statement_id = name + '-scrape-permission'
        try:
            lamb.add_permission(
                FunctionName=os.environ['BOBSLED_LAMBDA_ARN'],
                StatementId=perm_statement_id,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule['RuleArn'],
            )
        except ClientError:
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

        make_scraper_task(task['name'],
                          entrypoint,
                          image=task.get('image'),
                          memory_soft=task.get('memory_soft', 128),
                          environment=task.get('environment'),
                          force=force,
                          verbose=verbose,
                          )
        if task.get('cron'):
            make_cron_rule(task['name'],
                           'cron({})'.format(task['cron']),
                           task.get('enabled', True),
                           force=force,
                           verbose=verbose,
                           )


def run_task(task_name, started_by):
    ecs = boto3.client('ecs', region_name='us-east-1')

    print('running', task_name)

    response = ecs.run_task(
        cluster=os.environ['BOBSLED_ECS_CLUSTER'],
        count=1,
        taskDefinition=task_name,
        startedBy=started_by,
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
        task_definition={},     # TODO
        task_arn=response['tasks'][0]['taskArn'],
        ).save()
    return response
