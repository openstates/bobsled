from __future__ import print_function
import os
import shutil
import datetime
from collections import defaultdict, OrderedDict
from github import Github, UnknownObjectException
from jinja2 import Environment, PackageLoader
import boto3
import pymongo
from .utils import all_files
from .config import load_config


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
            if r.get('failure', False):
                has_failure = True
            else:
                has_success = True
        if has_success and has_failure:
            return 'other'
        elif has_success:
            return 'good'
        elif has_failure:
            return 'bad'
        else:
            return 'empty'


def get_last_runs(days=14):
    mc = pymongo.MongoClient(os.environ.get('BILLY_MONGO_HOST', 'localhost'))
    runs = mc.fiftystates.billy_runs.find(
        {'scraped.started':
         {'$gt': datetime.datetime.today() - datetime.timedelta(days=days)}
         }
    ).sort([('scraped.started', -1)])

    state_runs = defaultdict(lambda: defaultdict(RunList))

    for run in runs:
        rundate = run['scraped']['started'].date()
        state_runs[run['abbr']][rundate].add(run)

    return state_runs


def format_datetime(value):
    return value.strftime('%m/%d %H:%M:%S')


def format_time(value):
    return value.strftime('%H:%M:%S')


def render_jinja_template(template, **context):
    env = Environment(loader=PackageLoader('bobsled', 'templates'))
    env.filters['datetime'] = format_datetime
    env.filters['time'] = format_time
    template = env.get_template(template)
    return template.render(**context)


def render_runs(days, runs):
    today = datetime.date.today()
    days = [today - datetime.timedelta(days=n) for n in range(days)]
    runs = OrderedDict(sorted(runs.items()))
    return render_jinja_template('runs.html', runs=runs, days=days)


def render_run(runlist, date):
    return render_jinja_template('run.html', runlist=runlist, date=date)


def write_html(runs, output_dir, days=14):

    try:
        os.makedirs(output_dir)
    except OSError:
        pass

    with open(os.path.join(output_dir, 'index.html'), 'w') as out:
        out.write(render_runs(days, runs))

    for state, state_runs in runs.items():
        for date, rl in state_runs.items():
            if rl.runs:
                with open(os.path.join(output_dir, 'run-{}-{}.html'.format(state, date)), 'w') as out:
                    out.write(render_run(rl, date))

    shutil.copy(os.path.join(os.path.dirname(__file__), '../css/main.css'), output_dir)


def upload(dirname):
    s3 = boto3.resource('s3')
    config = load_config()
    CONTENT_TYPE = {'html': 'text/html',
                    'css': 'text/css'}

    for filename in all_files(dirname):
        ext = filename.rsplit('.', 1)[-1]
        content_type = CONTENT_TYPE.get(ext, '')
        s3.meta.client.put_object(
            ACL='public-read',
            Body=open(filename),
            Bucket=config['aws']['status_bucket'],
            Key=filename.replace(dirname + '/', ''),
            ContentType=content_type,
        )


def state_status(runs):
    CRITICAL = 2
    WARNING = 1

    for state, state_runs in runs.items():
        bad_in_a_row = 0
        exception = None
        args = None
        scraper = None

        for date, rl in sorted(state_runs.items(), reverse=True):
            if rl.status == 'good':
                break
            bad_in_a_row += 1
            if exception is None and rl.runs:
                args = ' '.join(rl.runs[0]['scraped']['args'])
                run_records = rl.runs[0]['scraped']['run_record']
                for rr in run_records:
                    if 'exception' in rr:
                        scraper = rr['type']
                        exception = rr['exception']

        if bad_in_a_row > CRITICAL:
            make_issue(state, bad_in_a_row, scraper, args, exception)
        elif bad_in_a_row > WARNING:
            print('warning for', state, bad_in_a_row, args, exception)



def check_status(do_upload=False):
    CHART_DAYS = 14

    output_dir = '/tmp/bobsled-output'
    runs = get_last_runs(CHART_DAYS)

    write_html(runs, output_dir, days=CHART_DAYS)
    state_status(runs)

    if do_upload:
        upload(output_dir)


def make_issue(state, days, scraper_type, args, exception):
    config = load_config()
    g = Github(config['github']['key'])
    r = g.get_repo('openstates/openstates')

    # ensure upper case
    state = state.upper()

    existing_issues = r.get_issues(creator='openstates-bot')
    for issue in existing_issues:
        if issue.title.startswith(state):
            print('issue already exists: #{}- {}'.format(
                issue.number, issue.title)
            )
            return

    ready = r.get_label('ready')
    try:
        automatic = r.get_label('automatic')
    except UnknownObjectException:
        automatic = r.create_label('automatic', '333333')

    since = datetime.date.today() - datetime.timedelta(days=days)

    body = '''State: {state} - scraper has been failing since {since}

Based on automated runs it appears that {state} has not run successfully in {days} days ({since}).

```{args}``` | **failed during {scraper_type}**

```
  {traceback}
```

Visit http://bobsled.openstates.org/ for more info.
'''.format(state=state, since=since, days=days, scraper_type=scraper_type, args=args, **exception)
    title='{} scraper failing since at least {}'.format(state, since)
    issue = r.create_issue(title=title, body=body, labels=[automatic, ready])
    print('created issue: #{} - {}'.format(issue.number, title))
