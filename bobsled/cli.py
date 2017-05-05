import os
import getpass
import click
import boto3
from .tasks import publish_task_definitions, run_task
from .status import update_status, get_log_for_run
from .dynamo import Run


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
def status():
    update_status()


@cli.command()
def init():
    # create table and ECS cluster
    Run.create_table(read_capacity_units=2, write_capacity_units=2, wait=True)
    ecs = boto3.client('ecs', region_name='us-east-1')
    ecs.create_cluster(clusterName=os.environ['BOBSLED_ECS_CLUSTER'])


if __name__ == '__main__':
    cli()
