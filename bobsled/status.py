from __future__ import print_function
import os
import re
import shutil
import datetime
from collections import defaultdict, OrderedDict

import boto3
from botocore.exceptions import ClientError
import github3

from bobsled.dynamo import Run, Status
from bobsled.templates import render_jinja_template, upload

OUTPUT_DIR = '/tmp/bobsled-output'


def update_status():
    try:
        os.makedirs(OUTPUT_DIR)
    except OSError:
        pass

    # update run records in database
    check_status()

    # update global view
    write_index_html()

    upload(OUTPUT_DIR)


def check_status():
    # check everything that's running
    runs = {r.task_arn: r for r in Run.status_index.query(Status.Running)}

    if not runs:
        return

    ecs = boto3.client('ecs', region_name='us-east-1')
    # we limit this to 100 for AWS, which is fine b/c 100 shouldn't be running at once
    # if somehow they are, a subsequent run will pick the rest up
    resp = ecs.describe_tasks(cluster=os.environ['BOBSLED_ECS_CLUSTER'],
                              tasks=list(runs.keys())[:100])

    # match status to runs
    for failure in resp['failures']:
        if failure['reason'] == 'MISSING':
            update_run_status(runs[failure['arn']])
        else:
            raise ValueError('unexpected status {}'.format(failure))

    for task in resp['tasks']:
        if task['lastStatus'] == 'STOPPED':
            update_run_status(runs[task['taskArn']])
        elif task['lastStatus'] in ('RUNNING', 'PENDING'):
            print('still running', runs[task['taskArn']])
        else:
            raise ValueError('unexpected status {}'.format(task))


def update_run_status(run):
    CRITICAL = 2

    try:
        logs = list(get_log_for_run(run))
    except ClientError:
        run.end = datetime.datetime.utcnow()
        run.status = Status.Missing
        run.save()
        return

    run.end = datetime.datetime.utcnow()

    if contains_error(logs):
        run.status = Status.Error
        print(run, '=> error')
        bad_in_a_row = get_failures(run.job)

        if bad_in_a_row >= CRITICAL:
            make_issue(run.job, bad_in_a_row, logs)
    else:
        run.status = Status.Success
        print(run, '=> success')

    run.save()

    write_day_html(run.job, run.start.date())


def get_failures(job):

    bad_in_a_row = 0
    # get recent runs in reverse-cron
    for run in Run.query(job, limit=8, scan_index_forward=False):
        if run.status == Status.Success:
            break
        elif run.status == Status.Error:
            bad_in_a_row += 1

    return bad_in_a_row


def get_log_for_run(run):
    logs = boto3.client('logs', region_name='us-east-1')

    pieces = dict(
        task_name=os.environ['BOBSLED_TASK_NAME'],
        family=run.job.lower(),
        task_id=run.task_id,
    )
    log_arn = '{family}/{task_name}/{task_id}'.format(**pieces)

    next = None

    while True:
        extra = {'nextToken': next} if next else {}
        events = logs.get_log_events(logGroupName=os.environ['BOBSLED_ECS_LOG_GROUP'],
                                     logStreamName=log_arn, **extra)
        next = events['nextForwardToken']

        if not events['events']:
            break

        for event in events['events']:
            yield event

        if not next:
            break


def contains_error(stream):
    ERROR_REGEX = re.compile(r'(CRITICAL)|(Exception)|(Traceback)')
    for line in stream:
        if ERROR_REGEX.findall(line['message']):
            return True


class RunList(object):

    def __init__(self):
        self.runs = []

    def add(self, run):
        self.runs.append(run)

    @property
    def status(self):
        has_success = False
        has_failure = False
        for r in self.runs:
            if r.status == Status.Error:
                has_failure = True
            elif r.status == Status.Success:
                has_success = True
        if has_success and has_failure:
            return 'other'
        elif has_success:
            return 'good'
        elif has_failure:
            return 'bad'
        else:
            return 'empty'


def write_index_html():
    chart_days = 14

    # get recent runs and group by day
    runs = Run.recent(chart_days)

    job_runs = defaultdict(lambda: defaultdict(RunList))

    for run in runs:
        rundate = run.start.date()
        job_runs[run.job][rundate].add(run)

    # render HTML
    today = datetime.date.today()
    days = [today - datetime.timedelta(days=n) for n in range(chart_days)]
    runs = OrderedDict(sorted(job_runs.items()))
    html = render_jinja_template('runs.html', runs=runs, days=days)

    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as out:
        out.write(html)
    shutil.copy(os.path.join(os.path.dirname(__file__), 'css/main.css'), OUTPUT_DIR)


def write_day_html(job, date):
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    end = datetime.datetime(date.year, date.month, date.day, 11, 59, 59)
    runs = list(Run.query(job, start__between=[start, end]))
    html = render_jinja_template('day.html', runs=runs, date=date)
    with open(os.path.join(OUTPUT_DIR,
                           'run-{}-{}.html'.format(job, date)), 'w') as out:
                    out.write(html)


def make_issue(job, days, logs):
    gh = github3.login(token=os.environ['BOBSLED_GITHUB_KEY'])
    r = gh.repository(os.environ['BOBSLED_GITHUB_USER'],
                      os.environ['BOBSLED_GITHUB_ISSUE_REPO'])

    # ensure upper case
    job = job.upper()

    existing_issues = r.iter_issues(labels='automatic', state='open')
    for issue in existing_issues:
        if issue.title.startswith(job):
            print('issue already exists: #{}- {}'.format(
                issue.number, issue.title)
            )
            return

    since = datetime.date.today() - datetime.timedelta(days=days-1)

    # show last 50 log lines
    logs = '\n'.join([l['message'] for l in logs[-50:]])

    body = '''{job} has been failing since {since}

Based on automated runs it appears that {job} has not run successfully in {days} days ({since}).


```
  {logs}
```

Visit http://bobsled.openstates.org/ for more info.
'''.format(job=job, since=since, days=days, logs=logs)
    title = '{} scraper failing since at least {}'.format(job, since)
    issue = r.create_issue(title=title, body=body, labels=['automatic', 'ready'])
    print('created issue: #{} - {}'.format(issue.number, title))
