import asyncio
import datetime
from .base import Status
from .core import bobsled


def parse_cron_segment(segment, star_equals):
    if segment == "*":
        return star_equals
    elif "," in segment:
        return sorted([int(n) for n in segment.split(",")])
    elif "-" in segment:
        start, end = segment.split("-")
        return list(range(int(start), int(end)+1))
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

    for minute in minutes:
        for hour in hours:
            next_time = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time > after:
                return next_time

    # no next time today, set to the first time but the next day
    next_time = next_time.replace(hour=hours[0], minute=minutes[0]) + datetime.timedelta(days=1)
    return next_time


async def run_service():
    await bobsled.run.persister.connect()
    for task in bobsled.tasks.get_tasks():
        for trigger in task.triggers:
            if 'cron' in trigger:
                print(task, next_cron(trigger['cron']))
    while True:
        pending = await bobsled.run.get_runs(status=Status.Pending)
        running = await bobsled.run.get_runs(status=Status.Running)
        print(f"pending={len(pending)} running={len(running)}")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_service())
