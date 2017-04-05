from __future__ import print_function
import os
import datetime
from jinja2 import Environment, PackageLoader
import boto3
import github3
from .utils import all_files


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


def render_run(runlist, date):
    return render_jinja_template('run.html', runlist=runlist, date=date)


def write_html(runs, output_dir, days=14):
    for state, state_runs in runs.items():
        for date, rl in state_runs.items():
            if rl.runs:
                with open(os.path.join(output_dir,
                                       'run-{}-{}.html'.format(state, date)), 'w') as out:
                    out.write(render_run(rl, date))


def state_status(runs):
    CRITICAL = 2
    WARNING = 1

    today = datetime.date.today()

    for state, state_runs in runs.items():
        bad_in_a_row = 0
        exception = None
        args = None
        scraper = None

        for date, rl in sorted(state_runs.items(), reverse=True):
            if rl.status == 'empty' and date == today:
                # don't count a missing run today against scraper
                continue
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

        if bad_in_a_row >= WARNING:
            print('warning for', state, bad_in_a_row)
            if exception and bad_in_a_row >= CRITICAL:
                make_issue(state, bad_in_a_row, scraper, args, exception)


    write_html(runs, output_dir, days=CHART_DAYS)


def make_issue(state, days, scraper_type, args, exception):
    gh = github3.login(token=os.environ['BOBSLED_GITHUB_KEY'])
    r = gh.repository(os.environ['BOBSLED_GITHUB_USER'],
                      os.environ['BOBSLED_GITHUB_ISSUE_REPO'])

    # ensure upper case
    state = state.upper()

    existing_issues = r.iter_issues(labels='automatic', state='open')
    for issue in existing_issues:
        if issue.title.startswith(state):
            print('issue already exists: #{}- {}'.format(
                issue.number, issue.title)
            )
            return

    since = datetime.date.today() - datetime.timedelta(days=days-1)

    body = '''State: {state} - scraper has been failing since {since}

Based on automated runs it appears that {state} has not run successfully in {days} days ({since}).

```{args}``` | **failed during {scraper_type}**

```
  {traceback}
```

Visit http://bobsled.openstates.org/ for more info.
'''.format(state=state, since=since, days=days, scraper_type=scraper_type, args=args, **exception)
    title = '{} scraper failing since at least {}'.format(state, since)
    issue = r.create_issue(title=title, body=body, labels=['automatic', 'ready'])
    print('created issue: #{} - {}'.format(issue.number, title))
