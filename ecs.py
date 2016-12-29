import glob
import boto3
import yaml

ecs = boto3.client('ecs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')


def load_config():
    config = yaml.load(open('config.yaml'))
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

    response = ecs.register_task_definition(
        family=family,
        containerDefinitions=[
            main_container
        ],
    )
    return response


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


def load_tasks():
    files = glob.glob('tasks/*.yml')
    for fn in files:
        with open(fn) as f:
            task = yaml.load(f)
            make_scraper_task(task['name'],
                              task['entrypoint'].split(),
                              memory_soft=task.get('memory_soft', 128),
                              environment=task.get('environment')
                              )
