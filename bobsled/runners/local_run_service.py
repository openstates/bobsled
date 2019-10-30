import datetime
import docker
from ..base import RunService, Status


class LocalRunService(RunService):
    def __init__(self, persister, environment, callbacks=None):
        self.client = docker.from_env()
        self.persister = persister
        self.environment = environment
        self.callbacks = callbacks or []

    def _get_container(self, run):
        if run.status == Status.Running:
            try:
                return self.client.containers.get(run.run_info["container_id"])
            except docker.errors.NotFound:
                return None

    def initialize(self, tasks):
        pass

    async def cleanup(self):
        n = 0
        for r in await self.persister.get_runs(status=[Status.Pending, Status.Running]):
            c = self._get_container(r)
            if c:
                c.remove(force=True)
                n += 1
        return n

    def start_task(self, task):
        env = {}
        if task.environment:
            env = self.environment.get_environment(task.environment).values
        container = self.client.containers.run(
            task.image,
            task.entrypoint if task.entrypoint else None,
            detach=True,
            environment=env,
        )
        return {"container_id": container.id}

    def stop(self, run):
        container = self._get_container(run)
        if not container:
            print("MISSING CONTAINER")
            return
        container.remove(force=True)

    async def update_status(self, run_id, update_logs=False):
        run = await self.persister.get_run(run_id)

        if run.status.is_terminal():
            return run

        container = self._get_container(run)
        if not container:
            # TODO: handle this
            print("missing container for", run)
            return run

        if container.status == "exited":
            resp = container.wait()
            if resp["Error"] or resp["StatusCode"]:
                run.status = Status.Error
            else:
                run.status = Status.Success

            run.logs = self.environment.mask_variables(container.logs().decode())
            run.end = datetime.datetime.utcnow().isoformat()
            run.exit_code = resp["StatusCode"]
            await self.persister.save_run(run)
            await self.trigger_callbacks(run)
            container.remove()

        elif run.status == Status.Running:
            if (
                run.run_info["timeout_at"]
                and datetime.datetime.utcnow().isoformat() > run.run_info["timeout_at"]
            ):
                run.logs = self.environment.mask_variables(container.logs().decode())
                container.remove(force=True)
                run.status = Status.TimedOut
                await self.persister.save_run(run)
                await self.trigger_callbacks(run)

            elif update_logs:
                run.logs = self.environment.mask_variables(container.logs().decode())
                await self.persister.save_run(run)
        return run
