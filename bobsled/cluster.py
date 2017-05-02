import os
import re
import datetime
import boto3


def create_cluster():
    ecs = boto3.client('ecs', region_name='us-east-1')
    ecs.create_cluster(clusterName=os.environ['BOBSLED_ECS_CLUSTER'])


def create_instance(instance_type):
    ec2 = boto3.client('ec2', region_name='us-east-1')

    ecs_user_data = '#!/bin/bash\necho ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(
        os.environ['BOBSLED_ECS_CLUSTER']
    )
    response = ec2.run_instances(
        ImageId=os.environ['BOBSLED_ECS_IMAGE_ID'],
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
    )
    return response


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
