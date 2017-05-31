import getpass
import click
import boto3
from botocore.exceptions import ClientError

from .tasks import publish_task_definitions, run_task
from .status import get_log_for_run
from .dynamo import Run
from . import config


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
@click.argument('job', nargs=1)
def logs(job):
    runs = list(Run.query(job, limit=1, scan_index_forward=False))
    click.echo('log for {}'.format(runs[0]))
    for ls in get_log_for_run(runs[0]):
        click.echo(ls['message'])


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
def init():
    # create table and ECS cluster
    Run.create_table(read_capacity_units=2, write_capacity_units=2, wait=True)
    ecs = boto3.client('ecs')
    ecs.create_cluster(clusterName=config.CLUSTER_NAME)
    logs = boto3.client('logs')
    try:
        logs.create_log_group(logGroupName=config.LOG_GROUP)
    except ClientError:
        # TODO: check error here
        pass
    # TODO: create ecsInstanceRole?


if __name__ == '__main__':
    cli()
