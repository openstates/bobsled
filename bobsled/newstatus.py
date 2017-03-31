from __future__ import print_function
import os
import re
import boto3
from bobsled.dynamo import Run, Status


def check_status():
    runs = {r.task_arn: r for r in Run.status_index.query('running')}

    ecs = boto3.client('ecs', region_name='us-east-1')
    resp = ecs.describe_tasks(cluster=os.environ['BOBSLED_ECS_CLUSTER'],
                              tasks=runs.keys())

    for failure in resp['failures']:
        if failure['reason'] == 'MISSING':
            update_status(runs[failure['arn']])
        else:
            raise ValueError('unexpected status {}'.format(failure))

    for task in resp['tasks']:
        if task['lastStatus'] == 'STOPPED':
            update_status(runs[task['taskArn']])
        elif task['lastStatus'] in ('RUNNING', 'PENDING'):
            print('still running', runs[task['taskArn']])
        else:
            raise ValueError('unexpected status {}'.format(task))


def update_status(run):
    logs = get_log_for_run(run)
    if contains_error(logs):
        run.status = Status.Error
        run.save()
        print(run, '=> error')
    else:
        run.status = Status.Success
        run.save()
        print(run, '=> success')


def get_log_for_run(run):
    logs = boto3.client('logs', region_name='us-east-1')

    pieces = dict(
        task_name=os.environ['BOBSLED_TASK_NAME'],
        family=run.job.lower(),
        task_id=run.task_arn.split('/')[-1],
    )
    log_arn = '{family}/{task_name}/{task_id}'.format(**pieces)

    next = None

    while True:
        extra = {'nextToken': next} if next else {}
        events = logs.get_log_events(logGroupName=os.environ['BOBSLED_ECS_LOG_GROUP'],
                                    logStreamName=log_arn, **extra)
        next = events['nextForwardToken']

        if not events['events']:
            break

        for event in events['events']:
            yield event

        if not next:
            break


def contains_error(stream):
    ERROR_REGEX = re.compile(r'CRITICAL|Exception')
    for line in stream:
        if ERROR_REGEX.findall(line['message']):
            return True
