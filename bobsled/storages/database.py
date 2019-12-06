import json
import attr
from databases import Database
import sqlalchemy
from ..base import Run, Status, Task


metadata = sqlalchemy.MetaData()
runs = sqlalchemy.Table(
    "bobsled_run",
    metadata,
    sqlalchemy.Column("uuid", sqlalchemy.String(length=50), primary_key=True),
    sqlalchemy.Column("status", sqlalchemy.String(length=50)),
    sqlalchemy.Column("task", sqlalchemy.String(length=100)),
    sqlalchemy.Column("start", sqlalchemy.String(length=50)),
    sqlalchemy.Column("end", sqlalchemy.String(length=50)),
    sqlalchemy.Column("logs", sqlalchemy.String()),
    sqlalchemy.Column("exit_code", sqlalchemy.Integer),
    sqlalchemy.Column("run_info_json", sqlalchemy.JSON()),
)
Tasks = sqlalchemy.Table(
    "bobsled_task",
    metadata,
    sqlalchemy.Column("name", sqlalchemy.String(length=100)),
    sqlalchemy.Column("image", sqlalchemy.String(length=100)),
    sqlalchemy.Column("tags", sqlalchemy.JSON()),
    sqlalchemy.Column("entrypoint", sqlalchemy.String(length=1000)),
    sqlalchemy.Column("environment", sqlalchemy.String(length=100)),
    sqlalchemy.Column("memory", sqlalchemy.Integer),
    sqlalchemy.Column("cpu", sqlalchemy.Integer),
    sqlalchemy.Column("enabled", sqlalchemy.Boolean),
    sqlalchemy.Column("timeout_minutes", sqlalchemy.Integer),
    sqlalchemy.Column("triggers", sqlalchemy.JSON()),
)


def _db_to_run(r):
    logs = ""
    if "logs" in r:
        logs = r["logs"]
    return Run(
        task=r["task"],
        status=Status[r["status"]],
        start=r["start"],
        end=r["end"],
        logs=logs,
        exit_code=r["exit_code"],
        run_info=json.loads(r["run_info_json"]),
        uuid=r["uuid"],
    )


def _run_to_db(r):
    values = attr.asdict(r)
    values["status"] = values["status"].name
    values["run_info_json"] = json.dumps(values.pop("run_info"))
    return values


def _task_to_db(t):
    values = attr.asdict(t)
    return values


def _db_to_task(row):
    return Task(**row)


class DatabaseStorage:
    def __init__(self, database_uri):
        self.database = Database(database_uri)

    async def connect(self):
        await self.database.connect()
        engine = sqlalchemy.create_engine(str(self.database.url))
        metadata.create_all(engine)

    async def add_run(self, run):
        query = runs.insert()
        await self.database.execute(query=query, values=_run_to_db(run))

    async def save_run(self, run):
        values = _run_to_db(run)
        uuid = values.pop("uuid")
        query = runs.update().where(runs.c.uuid == uuid).values(**values)
        await self.database.execute(query=query)

    async def get_run(self, run_id):
        query = runs.select().where(runs.c.uuid == run_id)
        row = await self.database.fetch_one(query=query)
        if row:
            return _db_to_run(row)

    async def get_runs(self, *, status=None, task_name=None, latest=None):
        query = sqlalchemy.select(
            [
                runs.c.uuid,
                runs.c.task,
                runs.c.status,
                runs.c.start,
                runs.c.end,
                runs.c.exit_code,
                runs.c.run_info_json,
            ]
        )
        query = query.order_by(runs.c.start.desc())
        if isinstance(status, Status):
            query = query.where(runs.c.status == status.name)
        elif isinstance(status, list):
            query = query.where(runs.c.status.in_(s.name for s in status))
        elif status:
            raise ValueError("status must be Status or list")
        if task_name:
            query = query.where(runs.c.task == task_name)
        if latest:
            query = query.limit(latest)
        rows = await self.database.fetch_all(query=query)

        return [_db_to_run(r) for r in reversed(rows)]

    async def get_tasks(self):
        query = Tasks.select()
        rows = await self.database.fetch_all(query=query)
        return [_db_to_task(r) for r in rows]

    async def get_task(self, name):
        query = Tasks.select().where(Tasks.c.name == name)
        row = await self.database.fetch_one(query=query)
        if row:
            return _db_to_task(row)

    async def set_tasks(self, tasks):
        for task in tasks:
            dbtask = _task_to_db(task)
            query = Tasks.insert()
            await self.database.execute(query=query, values=dbtask)
