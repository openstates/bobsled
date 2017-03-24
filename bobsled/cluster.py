import os
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
        #SubnetId='string',
        #DisableApiTermination=True|False,
        #InstanceInitiatedShutdownBehavior='stop'|'terminate',
        #AdditionalInfo='string',
    )
    return response



