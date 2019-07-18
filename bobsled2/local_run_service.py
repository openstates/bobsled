import datetime
import docker
from .base import RunService, Run, Status


class LocalRunService(RunService):
    def __init__(self):
        self.client = docker.from_env()
        self.runs = []

    def _get_container(self, run):
        if run.status == Status.Running:
            return self.client.containers.get(run.run_info["container_id"])

    def cleanup(self):
        for r in self.runs:
            c = self._get_container(r)
            if c:
                c.remove(force=True)

    def run_task(self, task):
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
        self.runs.append(run)
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
        return container.logs().decode()

    def get_run(self, run_id):
        run = [r for r in self.runs if r.uuid == run_id]
        if run:
            run = run[0]
            self.update_status(run)
            if run.status == Status.Running:
                run.logs = self.get_logs(run)
            return run

    def get_runs(self, *, status=None, task_name=None, update_status=False):
        runs = [r for r in self.runs]
        if status:
            runs = [r for r in runs if r.status == status]
        if task_name:
            runs = [r for r in runs if r.task == task_name]
        if update_status:
            for run in runs:
                self.update_status(run)
        return runs

    def register_crons(self, tasks):
        pass
