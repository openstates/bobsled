import attr
import enum
import uuid
import datetime
import typing
from .exceptions import AlreadyRunning


class Status(enum.Enum):
    Pending = 1
    Running = 2
    Error = 3
    Success = 4
    UserKilled = 5
    TimedOut = 6

    def is_terminal(self):
        return self.value in (3, 4, 5, 6)


@attr.s(auto_attribs=True)
class Environment:
    name: str
    values: typing.Dict[str, str]


@attr.s(auto_attribs=True)
class Trigger:
    cron: str


@attr.s(auto_attribs=True)
class Task:
    name: str
    image: str
    tags: typing.List[str] = []
    entrypoint: str = ""
    environment: str = ""
    memory: int = 512
    cpu: int = 256
    enabled: bool = True
    timeout_minutes: int = 0
    triggers: typing.List[Trigger] = []


@attr.s(auto_attribs=True)
class Run:
    task: str
    status: Status
    start: str = ""
    end: str = ""
    logs: str = ""
    exit_code: int = None
    run_info: typing.Dict[str, any] = {}
    uuid: str = attr.Factory(lambda: uuid.uuid4().hex)


@attr.s(auto_attribs=True)
class User:
    username: str
    password: str = "!"
    permissions: typing.List[str] = []


class EnvironmentStorage:
    def get_environments(self):
        return list(self.environments.values())

    def get_environment(self, name):
        return self.environments[name]

    def mask_variables(self, string):
        for env_name, env in self.environments.items():
            for var, value in env.values.items():
                string = string.replace(
                    str(value), f"**{env_name.upper()}/{var.upper()}**"
                )
        return string


class RunService:
    async def run_task(self, task):
        running = await self.get_runs(
            status=[Status.Pending, Status.Running], task_name=task.name
        )
        if running:
            raise AlreadyRunning()
        run_info = self.start_task(task)
        now = datetime.datetime.utcnow()
        timeout_at = ""
        if task.timeout_minutes:
            timeout_at = (
                now + datetime.timedelta(minutes=task.timeout_minutes)
            ).isoformat()
        run_info["timeout_at"] = timeout_at

        run = Run(task.name, Status.Running, start=now.isoformat(), run_info=run_info)
        await self.persister.add_run(run)
        return run

    async def trigger_callbacks(self, run):
        if run.status == Status.Success:
            for callback in self.callbacks:
                callback.on_success(run, self.persister)
        elif run.status == Status.Error:
            for callback in self.callbacks:
                callback.on_error(run, self.persister)

    async def get_runs(
        self, *, status=None, task_name=None, latest=None, update_status=False
    ):
        runs = await self.persister.get_runs(
            status=status, task_name=task_name, latest=latest
        )
        if update_status:
            for run in runs:
                await self.update_status(run.uuid)
        # sort runs old to new
        runs.sort(key=lambda r: r.start)
        return runs

    async def stop_run(self, run_id):
        run = await self.persister.get_run(run_id)
        if not run.status.is_terminal():
            self.stop(run)
            run.status = Status.UserKilled
            run.end = datetime.datetime.utcnow().isoformat()
            await self.persister.save_run(run)
