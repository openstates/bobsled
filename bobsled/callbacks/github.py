import github3
from ..base import Status


class GithubIssueCallback:
    def __init__(self, api_key, user, repo):
        self.api_key = api_key
        self.user = user
        self.repo = repo

        gh = github3.login(token=self.api_key)
        self.repo_obj = gh.repository(self.user, self.repo)

    async def on_success(self, latest_run, persister):
        issue = self.get_existing_issue(latest_run.task)
        if issue:
            issue.create_comment(f"closed via successful run on {latest_run.start}")
            issue.close()

    async def on_error(self, latest_run, persister):
        ERR_COUNT = 3

        latest_runs = (await persister.get_runs(task_name=latest_run.task))[:5]
        count = 0
        for r in latest_runs:
            if r.status == Status.Error:
                count += 1
            else:
                break

        if count >= ERR_COUNT:
            self.make_issue(latest_run, count, r)

    def get_existing_issue(self, task_name):
        existing_issues = self.repo_obj.iter_issues(labels="automatic", state="open")
        for issue in existing_issues:
            if issue.title.startswith(task_name):
                return issue

    def make_issue(self, latest_run, count, failure):
        if self.get_existing_issue(latest_run.task):
            return

        body = f"""{latest_run.task} has failed {count} since {failure.start}"""
        title = f"{latest_run.task} failing since at least {failure.start}"
        self.repo_obj.create_issue(
            title=title, body=body, labels=["automatic", "ready"]
        )
