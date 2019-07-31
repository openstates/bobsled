import pytest
from ..base import Run, Status
from ..runners import MemoryRunPersister
from ..callbacks.github import GithubIssueCallback


@pytest.mark.asyncio
async def test_github_on_error(mocker):
    mocker.patch("github3.login")
    gh = GithubIssueCallback(None, None, None)
    mocker.patch.object(gh, "make_issue")

    persister = MemoryRunPersister()
    a = Run("hello-world", Status.Error)
    b = Run("hello-world", Status.Error)
    c = Run("hello-world", Status.Error)
    d = Run("hello-world", Status.Error)

    # 2 failures, no GH call
    await persister.add_run(a)
    await persister.add_run(b)
    await gh.on_error(d, persister)
    gh.make_issue.assert_not_called()

    # 4 failures, GH call
    await persister.add_run(c)
    await persister.add_run(d)
    await gh.on_error(d, persister)
    gh.make_issue.assert_called_once_with(d, 4, d)


@pytest.mark.asyncio
async def test_github_on_success(mocker):
    mocker.patch("github3.login")
    gh = GithubIssueCallback(None, None, None)
    mocker.patch.object(gh, "get_existing_issue")

    persister = MemoryRunPersister()
    a = Run("hello-world", Status.Success)
    await gh.on_success(a, persister)

    gh.get_existing_issue.return_value.create_comment.assert_called()
