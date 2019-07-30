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

# memory options
# 256 (.25 vCPU) : 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB)
# 512 (.5 vCPU) : 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB)
# 1024 (1 vCPU) : 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB)
# 2048 (2 vCPU) : Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB)
# 4096 (4 vCPU) : Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB)



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
            timeout_at = (now + datetime.timedelta(minutes=task.timeout_minutes)).isoformat()
        run_info["timeout_at"] = timeout_at

        run = Run(
            task.name,
            Status.Running,
            start=now.isoformat(),
            run_info=run_info,
        )
        await self.persister.add_run(run)
        return run
