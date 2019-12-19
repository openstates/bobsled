import pytest
from ..base import Run, Status
from ..storages import InMemoryStorage
from ..callbacks.github import GithubIssueCallback


@pytest.mark.asyncio
async def test_github_on_error(mocker):
    mocker.patch("github3.login")
    gh = GithubIssueCallback(None, None, None)
    mocker.patch.object(gh, "make_issue")

    storage = InMemoryStorage()
    a = Run("hello-world", Status.Error)
    b = Run("hello-world", Status.Error)
    c = Run("hello-world", Status.Error)
    d = Run("hello-world", Status.Error)

    # 2 failures, no GH call
    await storage.add_run(a)
    await storage.add_run(b)
    await gh.on_error(b, storage)
    gh.make_issue.assert_not_called()

    # 4 failures, GH call
    await storage.add_run(c)
    await storage.add_run(d)
    await gh.on_error(d, storage)
    gh.make_issue.assert_called_once_with(d, 4, d)


@pytest.mark.asyncio
async def test_github_on_success(mocker):
    mocker.patch("github3.login")
    gh = GithubIssueCallback(None, None, None)
    mocker.patch.object(gh, "get_existing_issue")

    storage = InMemoryStorage()
    a = Run("hello-world", Status.Success)
    await gh.on_success(a, storage)

    gh.get_existing_issue.return_value.create_comment.assert_called()


def test_make_issue(mocker):
    mocker.patch("github3.login")
    gh = GithubIssueCallback(None, None, None)
    mocker.patch.object(gh.repo_obj, "create_issue")

    run = Run(
        "hello-world",
        Status.Error,
        logs="\n".join(str(n) for n in range(100)),
        start="2020-01-01",
    )
    gh.make_issue(run, 1, run)

    gh.repo_obj.create_issue.assert_called_once_with(
        title="hello-world failing since at least 2020-01-01",
        body="""hello-world has failed 1 times since 2020-01-01

Logs:
```
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
```
        """,
        labels=["automatic", "ready"],
    )
