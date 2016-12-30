from __future__ import print_function
import glob
import json
import datetime
import boto3
from botocore.exceptions import ClientError
import yaml

ecs = boto3.client('ecs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')
logs = boto3.client('logs', region_name='us-east-1')


def load_config():
    config = yaml.load(open('config.yaml'))

    config['tasks'] = []

    files = glob.glob('tasks/*.yml')
    for fn in files:
        with open(fn) as f:
            task = yaml.load(f)
            config['tasks'].append(task)

    return config


config = load_config()


def make_scraper_task(family,
                      entrypoint,
                      memory_soft=128,
                      name='openstates-scraper',
                      image='openstates/openstates',
                      environment=None,
                      #cpu=None,
                      #memory=None,
                      ):
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
            if existing['containerDefinitions'][0][key] != main_container[key]:
                create = True
                print('changing', key,
                      existing['containerDefinitions'][0][key],
                      main_container[key],
                      )
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


def run_task(task_definition, started_by):
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


def create_cluster():
    ecs.create_cluster(clusterName=config['ec2']['ecs_cluster'])


def create_instance(instance_type):
    ecs_user_data = '#!/bin/bash\necho ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(config['ec2']['ecs_cluster'])
    response = ec2.run_instances(
        ImageId=config['ec2']['ecs_image_id'],
        MinCount=1,
        MaxCount=1,
        KeyName=config['ec2']['key_name'],
        SecurityGroupIds=[config['ec2']['security_group_id']],
        UserData=ecs_user_data,
        InstanceType=instance_type,
        IamInstanceProfile={'Name': 'ecsInstanceRole'},
        #SubnetId='string',
        #DisableApiTermination=True|False,
        #InstanceInitiatedShutdownBehavior='stop'|'terminate',
        #AdditionalInfo='string',
    )
    return response


def upload_task_definitions(only=None):
    for task in config['tasks']:
        entrypoint = task['entrypoint']
        if not isinstance(entrypoint, list):
            entrypoint = entrypoint.split()
        if only and task['name'] != only:
            continue
        print('uploading', task['name'])
        make_scraper_task(task['name'],
                          entrypoint,
                          memory_soft=task.get('memory_soft', 128),
                          environment=task.get('environment')
                          )


def upload_schedules():
    for task in config['tasks']:
        if task['cron']:
            make_cron_rule(task['name'],
                           'cron({})'.format(task['cron']),
                           task.get('enabled', True)
                           )


def run_all_tasks(started_by):
    for task in config['tasks']:
        print('running', task['name'])
        run_task(task['name'], started_by)


def _get_log_streams(prefix=None):
    params = dict(logGroupName='openstates-scrapers',
                  #orderBy='LastEventTime',
                  )
    if prefix:
        params['logStreamNamePrefix'] = prefix
    streams = logs.describe_log_streams(**params)
    for s in streams['logStreams']:
        yield s


def print_streams(prefix=None):
    for s in _get_log_streams(prefix):
        print(s['logStreamName'],
              datetime.datetime.fromtimestamp(s['firstEventTimestamp']/1000).strftime('%Y-%m-%d %H:%M'))


def print_log(streamname):
    events = logs.get_log_events(logGroupName='openstates-scrapers',
                                 logStreamName=streamname)
    next = events['nextForwardToken']
    for event in events['events']:
        print(event['message'])


def print_latest_log(prefix):
    latest = None
    for s in _get_log_streams(prefix):
        print(s['logStreamName'],
              datetime.datetime.fromtimestamp(s['firstEventTimestamp']/1000).strftime('%Y-%m-%d %H:%M'))
        if latest is None or s['firstEventTimestamp'] > latest['firstEventTimestamp']:
            latest = s
    print('chose', latest['logStreamName'],
          datetime.datetime.fromtimestamp(latest['firstEventTimestamp']/1000).strftime('%Y-%m-%d %H:%M'))
    print_log(latest['logStreamName'])


def make_cron_rule(name, schedule, enabled):
    events = boto3.client('events', region_name='us-east-1')
    response = events.put_rule(
        Name=name,
        ScheduleExpression=schedule,
        State='ENABLED' if enabled else 'DISABLED',
        Description='run {} at {}'.format(name, schedule),
    )
    response = events.put_targets(
        Rule=name,
        Targets=[
            {
                'Id': name + '-scrape',
                'Arn': config['ec2']['lambda_arn'],
                'Input': json.dumps({'job': name})
            }
        ]
    )
