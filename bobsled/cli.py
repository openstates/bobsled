import os
import getpass
import click
from .logs import print_latest_log, get_log_streams
from .tasks import publish_task_definitions, run_task
from .awslambda import publish_function
from .status import update_status


@click.group()
def cli():
    pass


@cli.command()
@click.argument('dirname', nargs=1)
@click.argument('only', nargs=-1)
@click.option('--force/--no-force', default=False)
@click.option('-v', count=True)
def publish(dirname, only, force, v):
    publish_task_definitions(dirname, only, force, v > 0)


@cli.command()
@click.argument('prefix', nargs=1)
def logs(prefix):
    if not prefix:
        for ls in get_log_streams():
            click.echo(ls)
    else:
        print_latest_log(prefix)


@cli.command()
@click.argument('jobs', nargs=-1)
def run(jobs):
    who = getpass.getuser()
    if jobs:
        for job in jobs:
            run_task(job, who)
    else:
        click.secho('must include job name', fg='red')


@cli.command()
@click.option('--upload/--no-upload', default=False)
def status(upload):
    update_status()


@cli.command()
def init_lambda():
    funcs = {
        #'bobsled.handlers.echo': {
        #},
        'bobsled.handlers.update_status_handler': {
            'BOBSLED_ECS_CLUSTER': os.environ['BOBSLED_ECS_CLUSTER'],
            'BOBSLED_TASK_NAME': os.environ['BOBSLED_TASK_NAME'],
            'BOBSLED_ECS_LOG_GROUP': os.environ['BOBSLED_ECS_LOG_GROUP'],
            'BOBSLED_GITHUB_KEY': os.environ['BOBSLED_GITHUB_KEY'],
            'BOBSLED_GITHUB_USER': os.environ['BOBSLED_GITHUB_USER'],
            'BOBSLED_GITHUB_ISSUE_REPO': os.environ['BOBSLED_GITHUB_ISSUE_REPO'],
            'BOBSLED_STATUS_BUCKET': os.environ['BOBSLED_STATUS_BUCKET'],
        },
        #'bobsled.handlers.run_task_handler': {
        #    'BOBSLED_ECS_CLUSTER': os.environ['BOBSLED_ECS_CLUSTER'],
        #},
    }
    for func, env in funcs.items():
        publish_function(func.replace('.', '-'), func, func,
                         env, timeout=30, delete_first=True)

if __name__ == '__main__':
    cli()
