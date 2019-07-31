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


class RunService:
    async def run_task(self, task):
        # TODO handle waiting
        running = await self.get_runs(status=Status.Running, task_name=task.name)
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

    async def get_runs(self, *, status=None, task_name=None, update_status=False):
        runs = await self.persister.get_runs(status=status, task_name=task_name)
        if update_status:
            for run in runs:
                await self.update_status(run.uuid)
        # todo:? refresh runs dict?
        return runs

    async def stop_run(self, run_id):
        run = await self.persister.get_run(run_id)
        if not run.status.is_terminal():
            self.stop(run)
            run.status = Status.UserKilled
            run.end = datetime.datetime.utcnow().isoformat()
            await self.persister.save_run(run)