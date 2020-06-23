import github3
from ..base import Status


class GithubIssueCallback:
    def __init__(
        self,
        BOBSLED_GITHUB_API_KEY,
        BOBSLED_GITHUB_ISSUE_USER,
        BOBSLED_GITHUB_ISSUE_REPO,
    ):
        self.api_key = BOBSLED_GITHUB_API_KEY
        self.user = BOBSLED_GITHUB_ISSUE_USER
        self.repo = BOBSLED_GITHUB_ISSUE_REPO

        gh = github3.login(token=self.api_key)
        self.repo_obj = gh.repository(self.user, self.repo)

    async def on_success(self, latest_run, storage):
        issue = self.get_existing_issue(latest_run.task)
        if issue:
            issue.create_comment(
                f"closed via successful run on {latest_run.start[:10]}"
            )
            issue.close()

    async def on_error(self, latest_run, storage):
        task = await storage.get_task(name=latest_run.task)
        latest_runs = await storage.get_runs(task_name=latest_run.task, latest=5)
        count = 0
        for r in latest_runs:
            if r.status == Status.Error:
                count += 1
            else:
                break

        # if the number of failures is > threshold, and threshold is nonzero
        if count >= task.error_threshold > 0:
            self.make_issue(latest_run, count, r)

    def get_existing_issue(self, task_name):
        existing_issues = self.repo_obj.issues(labels="automatic", state="open")
        for issue in existing_issues:
            if issue.title.startswith(task_name):
                return issue

    def make_issue(self, latest_run, count, failure):
        if self.get_existing_issue(latest_run.task):
            return

        logs = "\n".join(latest_run.logs.splitlines()[-20:])
        body = f"""{latest_run.task} has failed {count} times since {failure.start[:10]}

Logs:
```
{logs}
```
        """
        title = f"{latest_run.task} failing since at least {failure.start[:10]}"
        self.repo_obj.create_issue(title=title, body=body, labels=["automatic"])
