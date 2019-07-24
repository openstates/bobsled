import datetime
import docker
from ..base import RunService, Run, Status
from .persisters import LocalRunPersister, DatabaseRunPersister


class LocalRunService(RunService):
    def __init__(self):
        self.client = docker.from_env()
        # self.persister = LocalRunPersister()
        self.persister = DatabaseRunPersister("sqlite:///test.db")

    def _get_container(self, run):
        if run.status == Status.Running:
            try:
                return self.client.containers.get(run.run_info["container_id"])
            except docker.errors.NotFound:
                return None

    async def cleanup(self):
        for r in await self.persister.get_runs():
            c = self._get_container(r)
            if c:
                c.remove(force=True)

    async def run_task(self, task):
        container = self.client.containers.run(
            task.image,
            task.entrypoint if task.entrypoint else None,
            detach=True
        )
        run = Run(
            task.name,
            Status.Running,
            start=datetime.datetime.utcnow().isoformat(),
            run_info={"container_id": container.id}
        )
        await self.persister.add_run(run)
        return run

    def update_status(self, run):
        if run.status in (Status.Success, Status.Error):
            return
        container = self._get_container(run)
        if container and container.status == "exited":
            resp = container.wait()
            if resp["Error"] or resp["StatusCode"]:
                run.status = Status.Error
            else:
                run.status = Status.Success
            run.exit_code = resp["StatusCode"]
            run.logs = container.logs().decode()
            container.remove()

    def get_logs(self, run):
        container = self._get_container(run)
        if container:
            return container.logs().decode()
        else:
            return ""

    async def get_run(self, run_id):
        run = await self.persister.get_run(run_id)
        if run:
            self.update_status(run)
            if run.status == Status.Running:
                run.logs = self.get_logs(run)
            return run

    async def get_runs(self, *, status=None, task_name=None, update_status=False):
        runs = await self.persister.get_runs(status=status, task_name=task_name)
        if update_status:
            for run in runs:
                self.update_status(run)
        return runs

    def register_crons(self, tasks):
        pass
