import os
import json
import datetime
import yaml
import pytest
import boto3

from unittest.mock import patch
from moto import mock_ec2, mock_ecs

from bobsled.cluster import (get_desired_status, create_instance,
                             get_killable_instances, get_instances, scale)
from bobsled import config


def setup_module(m):
    os.environ['BOBSLED_CLUSTER_NAME'] = 'bobsled-cluster'
    os.environ['BOBSLED_ECS_KEY_NAME'] = 'bobsled.pem'
    os.environ['BOBSLED_SECURITY_GROUP_ID'] = 'bobsled-ecs'
    with mock_ecs():
        ecs = boto3.client('ecs', region_name='us-east-1')
        ecs.create_cluster(clusterName=config.CLUSTER_NAME)


example_schedule = """schedule:
  # any time after 4am, OK to turn down instance load as jobs end
  - time: "04:00"
    instances: ['t2.medium']

  # by 6am we're done
  - time: "06:00"
    instances: []

  # at 23:30 let's get ready for the influx
  - time: "23:30"
    instances: ['t2.medium', 't2.medium']"""


def test_get_desired_status_between():
    schedule = yaml.load(example_schedule)['schedule']
    assert get_desired_status(schedule, datetime.time(5, 0)) == ['t2.medium']
    assert get_desired_status(schedule, datetime.time(7, 0)) == []


def test_get_desired_status_exact():
    schedule = yaml.load(example_schedule)['schedule']
    assert get_desired_status(schedule, datetime.time(4, 0)) == ['t2.medium']
    assert get_desired_status(schedule, datetime.time(6, 0)) == []
    assert get_desired_status(schedule, datetime.time(23, 30)) == ['t2.medium', 't2.medium']


def test_get_desired_status_before_first():
    schedule = yaml.load(example_schedule)['schedule']
    assert get_desired_status(schedule, datetime.time(0, 0)) == ['t2.medium', 't2.medium']


def test_get_desired_status_after_last():
    schedule = yaml.load(example_schedule)['schedule']
    assert get_desired_status(schedule, datetime.time(23, 50)) == ['t2.medium', 't2.medium']


@mock_ec2
def test_create_instance():
    create_instance('t2.medium')
    ec2 = boto3.client('ec2', 'us-east-1')
    resp = ec2.describe_instances(Filters=[
        {
            'Name': 'tag-key',
            'Values': [
                'bobsled',
            ]
        },
    ])
    resp = ec2.describe_instances()
    assert len(resp['Reservations']) == 1


@mock_ec2
def test_get_instances():
    create_instance('t2.medium')

    instances = get_instances()
    assert len(instances) == 1

    create_instance('t2.medium')
    create_instance('t2.micro')

    instances = get_instances()
    assert len(instances) == 3


@pytest.mark.skip(reason="""as of moto 0.4.31 the ECS mocking isn't complete

moto is missing runningTasksCount, pendingTasksCount, attributes on
the ECS instance, so get_killable_instances can't figure out
which instances have tasks
""")
@mock_ecs
@mock_ec2
def test_get_killable_instances():
    # this test is skipped
    ecs = boto3.client('ecs', 'us-east-1')

    resp = create_instance('t2.medium')
    # have to do this manually here, it is done automatically w/in the instance
    instance_id_document = json.dumps({'instanceId': resp['Instances'][0]['InstanceId']})
    ecs.register_container_instance(
        cluster=config.CLUSTER_NAME,
        instanceIdentityDocument=instance_id_document
    )

    # wrong type
    assert get_killable_instances('t2.small') == []
    # instance is idle
    assert len(get_killable_instances('t2.medium')) == 1

    # make a fake task
    ecs.register_task_definition(
        family='fake-task',
        containerDefinitions=[{
            'name': 'fake',
            'image': 'fake/fake',
            'essential': True,
            'memoryReservation': 128,
        }],
    )
    ecs.run_task(
        cluster=config.CLUSTER_NAME,
        count=1,
        taskDefinition='fake-task',
        startedBy='test',
    )

    # task will now be running on the instance
    assert len(get_killable_instances('t2.medium')) == 0


scale_schedule = """schedule:
  - time: "01:00"
    instances: ['t2.small']
  - time: "02:00"
    instances: ['t2.small', 't2.large']
  - time: "03:00"
    instances: ['t2.medium']
  - time: "06:00"
    instances: []"""


@mock_ec2
def test_scale_basic():
    schedule = yaml.load(scale_schedule)['schedule']

    # nothing exists at midnight
    scale(schedule, datetime.time(0, 0))
    assert get_instances() == []

    # get to 1am state
    scale(schedule, datetime.time(1, 5))
    instances = get_instances()
    assert len(instances) == 1
    assert instances[0]['InstanceType'] == 't2.small'


@mock_ec2
def test_scale_idempotent():
    schedule = yaml.load(scale_schedule)['schedule']

    # get to initial 1am state
    scale(schedule, datetime.time(1, 5))
    instances = get_instances()
    small_launch_time = instances[0]['LaunchTime']
    # at 1:30, no change
    scale(schedule, datetime.time(1, 30))
    instances = get_instances()

    assert len(instances) == 1
    assert instances[0]['InstanceType'] == 't2.small'
    # still the same instance
    assert instances[0]['LaunchTime'] == small_launch_time


@mock_ec2
def test_scale_up():
    schedule = yaml.load(scale_schedule)['schedule']

    # get to initial 1am state
    scale(schedule, datetime.time(1, 5))
    instances = get_instances()
    small_launch_time = instances[0]['LaunchTime']

    # at 2:00, scale up again
    scale(schedule, datetime.time(2, 0))
    instances = get_instances()
    assert len(instances) == 2
    assert {i['InstanceType'] for i in instances} == {'t2.small', 't2.large'}
    # original small is still there
    assert small_launch_time in {i['LaunchTime'] for i in instances}


@mock_ecs
@mock_ec2
def test_scale_down():
    schedule = yaml.load(scale_schedule)['schedule']

    # start at 2am state w/ 2 instances running
    scale(schedule, datetime.time(2, 0))
    old_instances = get_instances()
    assert len(old_instances) == 2

    # now go to 3am, where small & large are replaced by medium
    # but let's assume one is still in use, let's make sure it stick around
    def _get_killable(instance_type):
        old_instances[0]['ec2InstanceId'] = old_instances[0]['InstanceId']
        if instance_type == old_instances[0]['InstanceType']:
            return [old_instances[0]]
        return []

    with patch('bobsled.cluster.get_killable_instances', _get_killable):
        scale(schedule, datetime.time(3, 0))
    cur_instances = get_instances()
    assert len(cur_instances) == 2
    assert {i['InstanceType'] for i in cur_instances} == {'t2.medium',
                                                          old_instances[1]['InstanceType']}

    # now go to 5am, everything off and all instances in killable state
    def _get_killable(instance_type):
        for inst in cur_instances:
            inst['ec2InstanceId'] = inst['InstanceId']
            if instance_type == inst['InstanceType']:
                return [inst]
        return []

    with patch('bobsled.cluster.get_killable_instances', _get_killable):
        scale(schedule, datetime.time(7, 0))
    instances = get_instances()
    assert len(instances) == 0
