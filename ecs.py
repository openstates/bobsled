import boto3

ecs = boto3.client('ecs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

# Amazon's us-east-1 ecs optimized AMI (2016.09)
ECS_IMAGE_ID = 'ami-6df8fe7a'
ECS_USER_DATA = '#!/bin/bash\necho ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(ECS_CLUSTER)

# OS specific (not secret, but not useful to anyone outside OS)
ECS_CLUSTER = 'openstates-scrapers'
KEY_NAME = 'openstates-master'
SECURITY_GROUP_IDS = ['sg-74350609']


def make_scraper_task(family,
                      entrypoint,
                      *,
                      memory_soft=128,
                      log_stream_prefix=None,
                      name='openstates-scraper',
                      image='openstates/openstates'
                      #cpu=None,
                      #memory=None,
                      ):
    log_stream_prefix = family.lower()
    response = ecs.register_task_definition(
        family=family,
        containerDefinitions=[
            {
                'name': name,
                'image': image,
                'essential': True,
                'entryPoint': entrypoint,
                'memoryReservation': memory_soft,
                #'cpu': cpu,
                #'memory': memory,
                #'environment': [
                #    {
                #        'name': 'string',
                #        'value': 'string'
                #    },
                #],
                'logConfiguration': {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "openstates-scrapers",
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": log_stream_prefix
                    }
                },
            }
        ],
    )
    return response


def run_task(task_definition, started_by):
    response = ecs.run_task(
        cluster=ECS_CLUSTER,
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
    ecs.create_cluster(clusterName=ECS_CLUSTER)


def create_instance(instance_type):
    response = ec2.run_instances(
        ImageId=ECS_IMAGE_ID,
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_NAME,
        SecurityGroupIds=SECURITY_GROUP_IDS,
        UserData=ECS_USER_DATA,
        InstanceType=instance_type,
        IamInstanceProfile={'Name': 'ecsInstanceRole'},
        #Placement={
        #    'AvailabilityZone': 'string',
        #},
        #Monitoring={
        #    'Enabled': True|False
        #},
        #SubnetId='string',
        #DisableApiTermination=True|False,
        #InstanceInitiatedShutdownBehavior='stop'|'terminate',
        #PrivateIpAddress='string',
        #ClientToken='string',
        #AdditionalInfo='string',
        #EbsOptimized=True|False
    )
    return response


create_cluster()
create_instance('t2.medium')
make_scraper_task('NC', ['billy-update', 'nc', '--bills'], memory_soft=128)
run_task('scraper-pool', 'NC', 'os runbot')
