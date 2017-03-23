from __future__ import print_function
from bobsled.status import check_status
from bobsled.tasks import run_task


def echo(event, context):
    print(event, context)


def check_status_handler(event, context):
    check_status(do_upload=True)


def run_task_handler(event, context):
    run_task(event['job'], 'lambda')
