import click
from .logs import print_latest_log, get_log_streams
from .tasks import publish_task_definitions, run_task, run_all_tasks


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


if __name__ == '__main__':
    cli()
