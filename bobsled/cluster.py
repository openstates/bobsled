import boto3
from .config import get_config


def create_cluster():
    ecs = boto3.client('ecs', region_name='us-east-1')
    config = get_config()

    ecs.create_cluster(clusterName=config['ec2']['ecs_cluster'])


def create_instance(instance_type):
    ec2 = boto3.client('ec2', region_name='us-east-1')
    config = get_config()

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



