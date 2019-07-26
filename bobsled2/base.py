import attr
import enum
import uuid
import typing


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
    memory: int = 0
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
    def update_statuses(self):
        for r in self.get_runs(status=Status.Running):
            self.update_status(r)
