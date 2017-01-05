from __future__ import print_function

import json
import boto3
from botocore.exceptions import ClientError

from .config import load_config


def make_scraper_task(family,
                      entrypoint,
                      memory_soft=128,
                      name='openstates-scraper',
                      image='openstates/openstates',
                      environment=None,
                      #cpu=None,
                      #memory=None,
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
                print('changing {}: {} => {}'.format(key, oldval, newval))
    except ClientError:
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
        print('definition matches {family}:{revision}'.format(**existing))
    else:
        print('creating new task', family)


def make_cron_rule(name, schedule, enabled, config):
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
            print('updating rule', name, ' '.join(updating))
            create = True
    except ClientError:
        print('creating new cron rule', name, schedule)
        create = True

    if create:
        rule = events.put_rule(
            Name=name,
            ScheduleExpression=schedule,
            State=enabled,
            Description='run {} at {}'.format(name, schedule),
        )
        target = events.put_targets(
            Rule=name,
            Targets=[
                {
                    'Id': name + '-scrape',
                    'Arn': config['ec2']['lambda_arn'],
                    'Input': json.dumps({'job': name})
                }
            ]
        )
        perm_statement_id = name + '-scrape-permission'
        try:
            perm = lamb.add_permission(
                FunctionName=config['ec2']['lambda_arn'],
                StatementId=perm_statement_id,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule['RuleArn'],
            )
        except ClientError:
            # don't recreate permission if it is already there
            # could also
            # lamb.remove_permission(FunctionName=config['ec2']['lambda_arn'],
            #                     StatementId=perm_statement_id)
            # and recreate each time, but no value?
            pass
    else:
        print('no schedule change')


def publish_task_definitions(only=None):
    config = load_config()

    for task in config['tasks']:
        # convert entrypoint to list, break on spaces if needed
        entrypoint = task['entrypoint']
        if not isinstance(entrypoint, list):
            entrypoint = entrypoint.split()

        # shortcut for only adding certain task definitions
        if only and task['name'] not in only:
            continue

        print('==', task['name'], '===========')
        make_scraper_task(task['name'],
                          entrypoint,
                          memory_soft=task.get('memory_soft', 128),
                          environment=task.get('environment')
                          )
        if task.get('cron'):
            make_cron_rule(task['name'],
                           'cron({})'.format(task['cron']),
                           task.get('enabled', True),
                           config
                           )


def run_task(task_definition, started_by, config=None):
    if not config:
        config = load_config()
    ecs = boto3.client('ecs', region_name='us-east-1')

    print('running', task_definition)

    response = ecs.run_task(
        cluster=config['ec2']['ecs_cluster'],
        count=1,
        taskDefinition=task_definition,
        startedBy=started_by,
        #overrides={
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
        #},
    )
    return response


def run_all_tasks(started_by):
    config = load_config()
    for task in config['tasks']:
        run_task(task['name'], started_by, config)
