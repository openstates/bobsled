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
    )

    Run(task_name,
        task_definition=taskdef['taskDefinition'],
        task_arn=response['tasks'][0]['taskArn'],
        ).save()
    return response
