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
    Missing = 7

    def is_terminal(self):
        return self.value in (3, 4, 5, 6, 7)


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
    entrypoint: typing.List[str] = []
    environment: str = ""
    memory: int = 512
    cpu: int = 256
    enabled: bool = True
    timeout_minutes: int = 0
    error_threshold: int = 0
    triggers: typing.List[Trigger] = []
    next_tasks: typing.List[str] = []

    def __attrs_post_init__(self):
        if isinstance(self.entrypoint, str):
            self.entrypoint = self.entrypoint.split()


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
    password_hash: str
    permissions: typing.List[str] = []


class EnvironmentProvider:
    def mask_variables(self, string):
        for env_name in self.get_environment_names():
            env = self.get_environment(env_name)
            for var, value in env.values.items():
                string = string.replace(
                    str(value), f"**{env_name.upper()}/{var.upper()}**"
                )
        return string


class TaskProvider:
    async def update_tasks(self):
        raise NotImplementedError

    async def get_tasks(self):
        return await self.storage.get_tasks()

    async def get_task(self, name):
        return await self.storage.get_task(name)


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

        run = Run(
            task.name, self.STARTING_STATUS, start=now.isoformat(), run_info=run_info
        )
        await self.storage.add_run(run)
        return run

    async def _save_and_followup(self, run):
        await self.storage.save_run(run)
        if run.status == Status.Success:
            # start other jobs and do on success callback
            try:
                cur_task = await self.storage.get_task(run.task)
                for next_task in cur_task.next_tasks:
                    next_task = await self.storage.get_task(next_task)
                    await self.run_task(next_task)
            except KeyError as e:
                # in general we should probably handle this better, but it seems rare
                # and is likely only occuring in test situations where the running task
                # isn't registered
                print("missing task", e)

            for callback in self.callbacks:
                await callback.on_success(run, self.storage)

        elif run.status == Status.Error:
            for callback in self.callbacks:
                await callback.on_error(run, self.storage)

    async def get_runs(
        self, *, status=None, task_name=None, latest=None, update_status=False
    ):
        runs = await self.storage.get_runs(
            status=status, task_name=task_name, latest=latest
        )
        if update_status:
            for run in runs:
                await self.update_status(run.uuid)
        # sort runs old to new
        runs.sort(key=lambda r: r.start, reverse=True)
        return runs

    async def stop_run(self, run_id):
        run = await self.storage.get_run(run_id)
        if not run.status.is_terminal():
            self.stop(run)
            run.status = Status.UserKilled
            run.end = datetime.datetime.utcnow().isoformat()
            await self.storage.save_run(run)
