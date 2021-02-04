import asyncio
import attr
import pprint
import dateutil.parser
from datetime import timedelta
from bobsled.core import bobsled
from bobsled.base import Status


def recommend_frequency_for_task(runs):
    total_duration = timedelta(seconds=0)
    longest_duration = timedelta(seconds=0)
    for run in runs:
        start = dateutil.parser.parse(run.start)
        end = dateutil.parser.parse(run.end)
        duration = end - start
        total_duration += duration
        if duration > longest_duration:
            longest_duration = duration
    if longest_duration.seconds <= 60 * 10:
        return '0 */2 * * ?'
    elif longest_duration.seconds <= 60 * 60:
        return '0 */6 * * ?'
    else:
        return 'daily'


async def analyze_frequency():
    await bobsled.initialize()
    tasks = [attr.asdict(t) for t in await bobsled.storage.get_tasks()]
    results = await asyncio.gather(
        *[bobsled.run.get_runs(task_name=t["name"], latest=4) for t in tasks]
    )
    recommendations = []
    for task, latest_runs in zip(tasks, results):
        # make recommendations for scrape tasks that have runs
        if latest_runs and '-scrape' in task['name']:
            if all(run.status is Status.Success for run in latest_runs):
                recommendation = recommend_frequency_for_task(latest_runs)
            else:
                # a recent run failed, made a note of that
                recommendation = 'n/a - at least one recent task failed'
            if len(task['triggers']) > 0:
                current_schedule = task['triggers'][0]['cron']
            else:
                current_schedule = 'n/a'
            recommendations.append({
                'task': task['name'],
                'current_schedule': current_schedule,
                'recommended': recommendation
            })

    changed_recommendations = []
    for recommendation in recommendations:
        if recommendation['recommended'] != 'daily' and 'n/a' not in recommendation['recommended']\
                and recommendation['current_schedule'] != recommendation['recommended']:
            changed_recommendations.append(recommendation)

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(changed_recommendations)


def main():
    # asyncio.run(bobsled.initialize())  # this makes a threading problem if it's here
    asyncio.run(analyze_frequency())


if __name__ == "__main__":
    main()
