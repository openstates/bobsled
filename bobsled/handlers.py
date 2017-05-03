import os
import json
import datetime
from bobsled.status import update_status
from bobsled.tasks import run_task
from bobsled.cluster import scale


def update_status_handler(event, context):
    update_status()


def run_task_handler(event, context):
    run_task(event["job"], "lambda")


def scale_handler(event, context):
    schedule = json.loads(os.environ['BOBSLED_CLUSTER_SCHEDULE'])
    scale(schedule, datetime.datetime.utcnow().time())
