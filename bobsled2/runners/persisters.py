import json
import attr
from databases import Database
import sqlalchemy
from ..base import Run, Status


class MemoryRunPersister:
    def __init__(self):
        self.runs = []

    async def connect(self):
        pass

    async def add_run(self, run):
        self.runs.append(run)

    async def get_run(self, run_id):
        run = [r for r in self.runs if r.uuid == run_id]
        if run:
            return run[0]

    async def get_runs(self, *, status=None, task_name=None):
        runs = [r for r in self.runs]
        if status:
            runs = [r for r in runs if r.status == status]
        if task_name:
            runs = [r for r in runs if r.task == task_name]
        return runs


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


def _db_to_run(r):
    return Run(
        task=r.task,
        status=Status[r.status],
        start=r.start,
        end=r.end,
        logs=r.logs,
        exit_code=r.exit_code,
        run_info=json.loads(r.run_info_json),
        uuid=r.uuid,
    )


class DatabaseRunPersister:
    def __init__(self, database_uri):
        self.database = Database(database_uri)

    async def connect(self):
        await self.database.connect()
        engine = sqlalchemy.create_engine(str(self.database.url))
        metadata.create_all(engine)

    async def add_run(self, run):
        query = runs.insert()
        values = attr.asdict(run)
        values["status"] = values["status"].name
        values["run_info_json"] = json.dumps(values.pop("run_info"))
        await self.database.execute(query=query, values=values)

    async def get_run(self, run_id):
        query = runs.select().where(runs.c.uuid == run_id)
        row = await self.database.fetch_one(query=query)
        if row:
            return _db_to_run(row)

    async def get_runs(self, *, status=None, task_name=None):
        query = runs.select()
        if status:
            query = query.where(runs.c.status == status.name)
        if task_name:
            query = query.where(runs.c.task == task_name)
        rows = await self.database.fetch_all(query=query)
        return [_db_to_run(r) for r in rows]
