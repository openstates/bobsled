import datetime
import yaml
from bobsled.cluster import get_desired_status

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
