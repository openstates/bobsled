from __future__ import print_function
from bobsled.status import update_status
from bobsled.tasks import run_task


def echo(event, context):
    print(event, context)


def update_status_handler(event, context):
    update_status()


def run_task_handler(event, context):
    run_task(event['job'], 'lambda')
