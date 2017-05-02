import os
import datetime
import yaml
from bobsled.cluster import get_desired_status, create_instance, get_instances, scale
from moto import mock_ec2
import boto3


def setUp():
    os.environ['BOBSLED_ECS_CLUSTER'] = 'bobsled-cluster'
    os.environ['BOBSLED_ECS_IMAGE_ID'] = 'ami-abcdef12'
    os.environ['BOBSLED_ECS_KEY_NAME'] = 'bobsled.pem'
    os.environ['BOBSLED_SECURITY_GROUP_ID'] = 'bobsled-ecs'


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


@mock_ec2
def test_scale_down():
    schedule = yaml.load(scale_schedule)['schedule']

    # get to 2am state
    scale(schedule, datetime.time(2, 0))
    instances = get_instances()
    assert len(instances) == 2

    # now go to 3am, where small & large are replaced by medium
    scale(schedule, datetime.time(3, 0))
    instances = get_instances()
    assert len(instances) == 1
    assert {i['InstanceType'] for i in instances} == {'t2.medium'}

    # now go to 5am, everything off
    scale(schedule, datetime.time(5, 0))
    instances = get_instances()
    assert len(instances) == 0
