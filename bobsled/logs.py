import datetime
import boto3


def _fmt_time(ts):
    return datetime.datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M')


def get_log_streams(prefix=None):
    logs = boto3.client('logs', region_name='us-east-1')

    params = dict(logGroupName='openstates-scrapers',
                  # orderBy='LastEventTime',
                  )
    if prefix:
        params['logStreamNamePrefix'] = prefix
    streams = logs.describe_log_streams(**params)
    for s in streams['logStreams']:
        yield s


def print_streams(prefix=None):
    for s in get_log_streams(prefix):
        print(s['logStreamName'], _fmt_time(s['firstEventTimestamp']))


def print_log(streamname):
    logs = boto3.client('logs', region_name='us-east-1')

    events = logs.get_log_events(logGroupName='openstates-scrapers',
                                 logStreamName=streamname)
    # next = events['nextForwardToken']
    for event in events['events']:
        print(event['message'])


def print_latest_log(prefix):
    latest = None
    for s in get_log_streams(prefix.lower()):
        if (latest is None or
                s['firstEventTimestamp'] > latest['firstEventTimestamp']):
            latest = s
    print(_fmt_time(latest['firstEventTimestamp']))
    print_log(latest['logStreamName'])
