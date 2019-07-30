import github3


def make_issue(job, days, logs):
    gh = github3.login(token=config.GITHUB_KEY)
    r = gh.repository(config.GITHUB_USER, config.GITHUB_ISSUE_REPO)

    # ensure upper case
    job = job.upper()

    existing_issues = r.iter_issues(labels='automatic', state='open')
    for issue in existing_issues:
        if issue.title.startswith(job):
            print('issue already exists: #{}- {}'.format(
                issue.number, issue.title)
            )
            return

    since = datetime.date.today() - datetime.timedelta(days=days-1)

    # show last 50 log lines
    logs = '\n'.join([l['message'] for l in logs[-50:]])

    body = '''{job} has been failing since {since}

Based on automated runs it appears that {job} has not run successfully in {days} days ({since}).


```
  {logs}
```

Visit http://{bucket} for more info.
'''.format(job=job, since=since, days=days, logs=logs, bucket=config.STATUS_BUCKET)
    title = '{} failing since at least {}'.format(job, since)
    issue = r.create_issue(title=title, body=body, labels=['automatic', 'ready'])
    print('created issue: #{} - {}'.format(issue.number, title))
