def make_cron_rule(name, schedule, enabled, force=False, verbose=False):
    events = boto3.client('events')
    lamb = boto3.client('lambda')

    enabled = 'ENABLED' if enabled else 'DISABLED'
    create = False

    try:
        old_rule = events.describe_rule(Name=name)
        updating = []
        if schedule != old_rule['ScheduleExpression']:
            updating.append('schedule')
        if enabled != old_rule['State']:
            updating.append('enabled')
        if updating:
            print('{}: updating rule'.format(name), ' '.join(updating))
            create = True
    except ClientError:
        print('{}: creating new cron rule'.format(name), schedule)
        create = True

    if force:
        create = True

    # figure out full lambda arn
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = events.meta.region_name
    lambda_arn = 'arn:aws:lambda:{}:{}:function:bobsled-dev'.format(region, account_id)

    if create:
        rule = events.put_rule(
            Name=name,
            ScheduleExpression=schedule,
            State=enabled,
            Description='run {} at {}'.format(name, schedule),
        )
        events.put_targets(
            Rule=name,
            Targets=[
                {
                    'Id': name + '-job',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'job': name,
                        'command': 'bobsled.tasks.run_task_handler',
                    })
                }
            ]
        )
        perm_statement_id = name + '-job-permission'
        try:
            lamb.add_permission(
                FunctionName=lambda_arn,
                StatementId=perm_statement_id,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule['RuleArn'],
            )
        except ClientError as e:
            print(e)
            # don't recreate permission if it is already there
            pass
    elif verbose:
        print('{}: no schedule change'.format(name))