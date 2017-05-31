import os
import shutil
import datetime
from collections import defaultdict, OrderedDict

import boto3
from botocore.exceptions import ClientError
import github3

from bobsled.dynamo import Run, Status
from bobsled.templates import render_jinja_template, upload
from . import config

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

    ecs = boto3.client('ecs')
    # we limit this to 100 for AWS, which is fine b/c 100 shouldn't be running at once
    # if somehow they are, a subsequent run will pick the rest up
    resp = ecs.describe_tasks(cluster=config.CLUSTER_NAME,
                              tasks=list(runs.keys())[:100])

    # match status to runs
    for failure in resp['failures']:
        if failure['reason'] == 'MISSING':
            # this shouldn't happen if we're checking frequently enough
            update_run_status(runs[failure['arn']], None)
        else:
            raise ValueError('unexpected status {}'.format(failure))

    for task in resp['tasks']:
        if task['lastStatus'] == 'STOPPED':
            update_run_status(runs[task['taskArn']], task)
        elif task['lastStatus'] in ('RUNNING', 'PENDING'):
            print('still running', runs[task['taskArn']])
        else:
            raise ValueError('unexpected status {}'.format(task))


def update_run_status(run, task):
    CRITICAL = 2

    # this means that the record was missing
    if not task:
        run.status = Status.Missing
        print(run, '=> missing')
    else:
        try:
            # check exit code
            exit_code = task['containers'][0]['exitCode']
            if exit_code == 0:
                run.status = Status.Success
                print(run, '=> success')
            else:
                run.status = Status.Error
                run.status_note = 'Exit Code: {}'.format(exit_code)
                print(run, '=> error')

                # if we had a job failure, maybe file an issue
                bad_in_a_row = get_failures(run.job)
                if bad_in_a_row >= CRITICAL:
                    logs = list(get_log_for_run(run))
                    make_issue(run.job, bad_in_a_row, logs)
        except KeyError:
            # usually this means we had resource exhaustion
            run.status = Status.SystemError
            run.status_note = task['containers'][0]['reason']
            print(run, '=> systemerror')

    # save our new status
    run.end = datetime.datetime.utcnow()
    run.save()

    write_day_html(run.job, run.start.date())


def get_failures(job):
    bad_in_a_row = 0
    # get recent runs in reverse-cron
    for run in Run.query(job, limit=8, scan_index_forward=False):
        # how many Errors do we see until there's a success?
        # note that we intentionally ignore SystemError and Missing here
        # as they shouldn't count for or against the error count
        if run.status == Status.Success:
            break
        elif run.status == Status.Error:
            bad_in_a_row += 1

    return bad_in_a_row


def get_log_for_run(run):
    logs = boto3.client('logs')

    env_replace = {e['value']: '**{}**'.format(e['name'])
                   for e in run.task_definition['containerDefinitions'][0]['environment']}

    pieces = dict(
        task_name=config.TASK_NAME,
        family=run.job.lower(),
        task_id=run.task_id,
    )
    log_arn = '{family}/{task_name}/{task_id}'.format(**pieces)
    print(log_arn)

    next = None

    while True:
        extra = {'nextToken': next} if next else {}
        try:
            events = logs.get_log_events(logGroupName=config.LOG_GROUP,
                                         logStreamName=log_arn, **extra)
        except ClientError:
            yield {'message': 'no logs'}
            break
        next = events['nextForwardToken']

        if not events['events']:
            break

        for event in events['events']:
            for k, v in env_replace.items():
                event['message'] = event['message'].replace(k, v)
            yield event

        if not next:
            break


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
    print(job, date)
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    end = datetime.datetime(date.year, date.month, date.day, 11, 59, 59)
    runs = list(Run.query(job, start__between=[start, end]))
    for run in runs:
        logs = list(get_log_for_run(run))
        run.logs = '\n'.join([l['message'] for l in logs[-100:]])
    print(runs)
    html = render_jinja_template('day.html', runs=runs, date=date)
    with open(os.path.join(OUTPUT_DIR, 'run-{}-{}.html'.format(job, date)), 'w') as out:
        out.write(html)


def make_issue(job, days, logs):
    gh = github3.login(token=config.GITHUB_KEY)
    r = gh.repository(config.GITHUB_USER, config.GITHUB_ISSUE_REPO)

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

Visit http://{bucket} for more info.
'''.format(job=job, since=since, days=days, logs=logs, bucket=config.STATUS_BUCKET)
    title = '{} failing since at least {}'.format(job, since)
    issue = r.create_issue(title=title, body=body, labels=['automatic', 'ready'])
    print('created issue: #{} - {}'.format(issue.number, title))
