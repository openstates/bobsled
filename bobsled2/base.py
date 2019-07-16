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
    tags: typing.List[str]
    image: str
    entrypoint: str
    memory: int
    enabled: bool
    triggers: typing.List[Trigger]


@attr.s(auto_attribs=True)
class Run:
    status: Status
    task: str
    start: str
    end: str
    exit_code: int
    run_info: typing.Dict[str, any]
    uuid: str = attr.Factory(uuid.uuid4)


class EnvironmentService:
    def get_environments(self):
        pass

    def get_environment(self, name):
        pass


class TaskService:
    def load_tasks(self):
        pass

    def add_task(self, task):
        pass

    def delete_task(self, task):
        pass

    def get_tasks(self):
        pass


class RunService:
    def register_crons(self, tasks):
        pass

    def run_task(self, task, trigger):
        pass

    def update_status(self):
        pass

    def get_logs(self, task, stream=False):
        pass

    def get_runs(self, status, count):
        pass


# # startup
# tasks = RepoTaskService("https://example.git")
# ecs = ECSRunService(...)
# ecs.register_crons(tasks)


# # homepage
# ecs.get_runs() # waiting, running, finished
# tasks.get_tasks()


# # task page
# ecs.get_logs(task)
