zappa publish
    -> push code to AWS

bobsled init
    -> create AWS infrastructure
        -> DynamoDB table
        -> ECS cluster

bobsled publish
    -> create tasks
    -> create schedule entries that invoke run_task directly
    -> write scale schedule somewhere that next task can read

bobsled run
    -> invoke run_task directly


bobsled.status.update_status()
bobsled.tasks.run_task(name, who_ran)


schedule = json.loads(os.environ['BOBSLED_CLUSTER_SCHEDULE'])
scale(schedule, datetime.datetime.utcnow().time())
