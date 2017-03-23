import getpass
import click
from .logs import print_latest_log, get_log_streams
from .tasks import publish_task_definitions, run_task
from .awslambda import publish_function
from .status import check_status


@click.group()
def cli():
    pass


@cli.command()
@click.argument('only', nargs=-1)
def publish(only):
    click.echo('publishing {} to AWS'.format(', '.join(only)
                                             if only else 'tasks'))
    publish_task_definitions(only)


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
    check_status(upload)
    if upload:
        click.echo('uploaded to S3')

@cli.command()
def init_lambda():
    funcs = ('bobsled.handlers.echo',
             'bobsled.handlers.check_status_handler',
             'bobsled.handlers.run_task_handler',
             )
    for func in funcs:
        publish_function(func.replace('.', '-'), func, func, timeout=30, delete_first=True)

if __name__ == '__main__':
    cli()
