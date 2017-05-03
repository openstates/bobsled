import os
import re
import datetime
import logging
from collections import Counter
import boto3

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_cluster():
    ecs = boto3.client('ecs', region_name='us-east-1')
    ecs.create_cluster(clusterName=os.environ['BOBSLED_ECS_CLUSTER'])


def create_instance(instance_type):
    ec2 = boto3.client('ec2', region_name='us-east-1')

    ecs_user_data = '#!/bin/bash\necho ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(
        os.environ['BOBSLED_ECS_CLUSTER']
    )
    response = ec2.run_instances(
        ImageId=os.environ.get('BOBSLED_ECS_IMAGE_ID', 'ami-275ffe31'),
        MinCount=1,
        MaxCount=1,
        KeyName=os.environ['BOBSLED_ECS_KEY_NAME'],
        SecurityGroupIds=[os.environ['BOBSLED_SECURITY_GROUP_ID']],
        UserData=ecs_user_data,
        InstanceType=instance_type,
        IamInstanceProfile={'Name': 'ecsInstanceRole'},
        # SubnetId='string',
        # DisableApiTermination=True|False,
        # InstanceInitiatedShutdownBehavior='stop'|'terminate',
        # AdditionalInfo='string',
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'bobsled',
                    'Value': 'true'
                },
            ]
        }]
    )
    # in theory these lines aren't needed, but moto doesn't work without them
    instance_id = response['Instances'][0]['InstanceId']
    ec2.create_tags(Resources=[instance_id],
                    Tags=[{'Key': 'bobsled', 'Value': 'true'}])
    return response


def get_instances():
    ec2 = boto3.client('ec2', 'us-east-1')
    resp = ec2.describe_instances(Filters=[
        {'Name': 'tag-key', 'Values': ['bobsled']},
        {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
     ])

    instances = []
    for reservation in resp['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance)

    return instances


def get_killable_instances(instance_type):
    ecs = boto3.client('ecs', region_name='us-east-1')
    arns = ecs.list_container_instances(cluster=os.environ['BOBSLED_ECS_CLUSTER']
                                        )['containerInstanceArns']
    resp = ecs.describe_container_instances(cluster=os.environ['BOBSLED_ECS_CLUSTER'],
                                            containerInstances=arns)
    resp = resp['containerInstances']

    logger.debug('checking for killable %s among %s candidates', instance_type, len(arns))

    killable = []
    for inst in resp:
        # instance is idle
        logger.debug('checking %s %s %s', inst['ec2InstanceId'], inst['pendingTasksCount'],
                     inst['runningTasksCount'])

        if inst['pendingTasksCount'] == 0 and inst['runningTasksCount'] == 0:
            # check if it is the right size
            for attrib in inst['attributes']:
                if attrib['name'] == 'ecs.instance-type' and attrib['value'] == instance_type:
                    killable.append(inst)

    return killable


def _parse_time(time):
    h, m = re.match(r'([0-2]\d):([0-5]\d)', time).groups()
    return datetime.time(int(h), int(m))


def get_desired_status(schedule, time):
    last_time = None
    last_result = schedule[-1]['instances']

    # walk through schedule and break when we're in the right slot
    # being in the right slot means we should return the previous (start time)
    # instances array
    for entry in schedule:
        entry_time = _parse_time(entry['time'])

        # we're before or equal to the start time
        if last_time is None:
            if time < entry_time:
                break
        elif last_time < time < entry_time:
            break

        last_result = entry['instances']

    return last_result


def scale(schedule, time):
    ec2 = boto3.client('ec2', region_name='us-east-1')

    desired_status = get_desired_status(schedule, time)

    instances = get_instances()
    instance_types = [inst['InstanceType'] for inst in instances]

    logger.info('scaling from %s to %s', instance_types, desired_status)

    to_create = Counter(desired_status) - Counter(instance_types)
    to_delete = Counter(instance_types) - Counter(desired_status)

    for inst_type, num in to_create.items():
        for n in range(num):
            logger.info('creating %s', inst_type)
            create_instance(inst_type)

    for inst_type, num in to_delete.items():
        killable = get_killable_instances(inst_type)
        logger.debug('found %s killable', len(killable))
        # kill no more than num idle instances
        for instance in killable[:num]:
            logger.info('terminating %s', instance['ec2InstanceId'])
            ec2.terminate_instances(InstanceIds=[instance['ec2InstanceId']])
