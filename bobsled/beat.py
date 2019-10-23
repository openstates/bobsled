import asyncio
import datetime
import zmq
from .base import Status
from .core import bobsled
from .exceptions import AlreadyRunning


def parse_cron_segment(segment, star_equals):
    if segment == "*":
        return star_equals
    elif "," in segment:
        return sorted([int(n) for n in segment.split(",")])
    elif "-" in segment:
        start, end = segment.split("-")
        return list(range(int(start), int(end) + 1))
    elif segment.isdigit():
        return [int(segment)]


def next_cron(cronstr, after=None):
    minute, hour, day, month, dow = cronstr.split()

    minutes = parse_cron_segment(minute, list(range(60)))
    hours = parse_cron_segment(hour, list(range(24)))

    # TODO: handle things that don't run every day
    assert day == "*"
    assert month == "*"
    assert dow == "?"

    if not after:
        after = datetime.datetime.utcnow()
    next_time = None

    for hour in hours:
        for minute in minutes:
            next_time = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time > after:
                return next_time

    # no next time today, set to the first time but the next day
    next_time = next_time.replace(
        hour=hours[0], minute=minutes[0]
    ) + datetime.timedelta(days=1)
    return next_time


def next_run_for_task(task):
    for trigger in task.triggers:
        if "cron" in trigger:
            return next_cron(trigger["cron"])


LOG_FILE = "/tmp/bobsled-beat.log"
SOCKET_FILE = "/tmp/bobsled-beat"


async def run_service():
    await bobsled.run.persister.connect()

    lf = open(LOG_FILE, "w")

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("ipc://" + SOCKET_FILE)

    next_run_list = {}
    for task in bobsled.tasks.get_tasks():
        if not task.enabled:
            continue
        next_run = next_run_for_task(task)
        if next_run:
            next_run_list[task.name] = next_run
            print(task.name, "next run at", next_run, file=lf, flush=True)

    while True:
        pending = await bobsled.run.get_runs(status=Status.Pending)
        running = await bobsled.run.get_runs(status=Status.Running)
        utcnow = datetime.datetime.utcnow()

        msg = f"{utcnow}: pending={len(pending)} running={len(running)}"
        socket.send_string(msg)
        print(msg, file=lf, flush=True)

        # parallel updates from all running tasks
        await asyncio.gather(
            *[
                bobsled.run.update_status(run.uuid, update_logs=True)
                for run in running + pending
            ]
        )

        # TODO: could improve by basing next run time on last run instead of using utcnow
        for task_name, next_run in next_run_list.items():
            if next_run <= utcnow:
                # update next run time
                next_run_list[task_name] = next_run_for_task(task)
                try:
                    run = await bobsled.run.run_task(task)
                    task = bobsled.tasks.get_task(task_name)
                    msg = f"started {task_name}: {run}.  next run at {next_run_list[task_name]}"
                except AlreadyRunning:
                    msg = f"{task_name}: already running.  next run at {next_run_list[task_name]}"
                socket.send_string(msg)
                print(msg, file=lf, flush=True)

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run_service())
