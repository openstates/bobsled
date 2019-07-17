import attr
import enum
import uuid
import typing

class Status(enum.Enum):
    Pending = 1
    Running = 2
    Error = 3
    Success = 4


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
    triggers: typing.List[Trigger] = []


@attr.s(auto_attribs=True)
class Run:
    task: str
    status: Status
    start: str = ""
    end: str = ""
    exit_code: int = None
    run_info: typing.Dict[str, any] = {}
    uuid: str = attr.Factory(uuid.uuid4)


class EnvironmentService:
    def get_environments(self):
        pass

    def get_environment(self, name):
        pass


class TaskService:
    def get_tasks(self):
        pass

    def get_task(self, name):
        pass


class RunService:
    def update_statuses(self):
        for r in self.get_runs(status=Status.Running):
            self.update_status(r)

    def run_task(self, task, trigger):
        pass

    def update_status(self):
        pass

    def get_logs(self, run):
        pass

    def get_runs(self, *, status, task_name):
        pass

    def register_crons(self, tasks):
        pass
