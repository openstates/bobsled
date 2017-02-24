import os
import shutil
import datetime
from collections import defaultdict, OrderedDict
import pymongo
from jinja2 import Environment, PackageLoader


def get_last_runs(days=14):
    mc = pymongo.MongoClient(os.environ.get('BILLY_MONGO_HOST', 'localhost'))
    runs = mc.fiftystates.billy_runs.find(
        {'scraped.started':
         {'$gt': datetime.datetime.today() - datetime.timedelta(days=days)}
         }
    )

    state_runs = defaultdict(lambda: defaultdict(list))

    for run in runs:
        rundate = run['scraped']['started'].date()
        state_runs[run['abbr']][rundate].append(run)

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


def render_run(run):
    return render_jinja_template('run.html', run=run)


def write_html(days=14):
    output_dir = '/tmp/bobsled-output'

    try:
        os.makedirs(output_dir)
    except OSError:
        pass

    runs = get_last_runs(days)
    with open(os.path.join(output_dir, 'index.html'), 'w') as out:
        out.write(render_runs(days, runs))

    for state, state_runs in runs.items():
        for date, runs in state_runs.items():
            for run in runs:
                with open(os.path.join(output_dir, 'run{}.html'.format(run['_id'])), 'w') as out:
                    out.write(render_run(run))

    shutil.copy(os.path.join(os.path.dirname(__file__), '../css/main.css'), output_dir)


if __name__ == '__main__':
    write_html()
