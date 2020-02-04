import json
import attr
import sqlalchemy
from databases import Database
from ..base import Run, Status, Task, Trigger, User
from ..utils import hash_password, verify_password


metadata = sqlalchemy.MetaData()
Tasks = sqlalchemy.Table(
    "bobsled_task",
    metadata,
    sqlalchemy.Column("name", sqlalchemy.String(length=100), primary_key=True),
    sqlalchemy.Column("image", sqlalchemy.String(length=100)),
    sqlalchemy.Column("tags", sqlalchemy.JSON()),
    sqlalchemy.Column("entrypoint", sqlalchemy.ARRAY(sqlalchemy.String(length=1000))),
    sqlalchemy.Column("environment", sqlalchemy.String(length=100)),
    sqlalchemy.Column("memory", sqlalchemy.Integer),
    sqlalchemy.Column("cpu", sqlalchemy.Integer),
    sqlalchemy.Column("enabled", sqlalchemy.Boolean),
    sqlalchemy.Column("timeout_minutes", sqlalchemy.Integer),
    sqlalchemy.Column("triggers", sqlalchemy.JSON()),
    sqlalchemy.Column("next_tasks", sqlalchemy.ARRAY(sqlalchemy.String(length=100))),
)
Runs = sqlalchemy.Table(
    "bobsled_run",
    metadata,
    sqlalchemy.Column("uuid", sqlalchemy.String(length=50), primary_key=True),
    sqlalchemy.Column("status", sqlalchemy.String(length=50)),
    sqlalchemy.Column(
        "task", sqlalchemy.String(length=100), sqlalchemy.ForeignKey(Tasks.c.name)
    ),
    sqlalchemy.Column("start", sqlalchemy.String(length=50)),
    sqlalchemy.Column("end", sqlalchemy.String(length=50)),
    sqlalchemy.Column("logs", sqlalchemy.String()),
    sqlalchemy.Column("exit_code", sqlalchemy.Integer),
    sqlalchemy.Column("run_info_json", sqlalchemy.JSON()),
)
Users = sqlalchemy.Table(
    "bobsled_user",
    metadata,
    sqlalchemy.Column("username", sqlalchemy.String(length=100)),
    sqlalchemy.Column("password", sqlalchemy.String(length=100)),
    sqlalchemy.Column("permissions", sqlalchemy.ARRAY(sqlalchemy.String(length=100))),
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
    vals = dict(**row)
    vals["triggers"] = [Trigger(**t) for t in row["triggers"]]
    return Task(**vals)


class DatabaseStorage:
    def __init__(self, BOBSLED_DATABASE_URI):
        self.database = Database(BOBSLED_DATABASE_URI)

    async def connect(self):
        await self.database.connect()
        engine = sqlalchemy.create_engine(str(self.database.url))
        metadata.create_all(engine)

    async def add_run(self, run):
        query = Runs.insert()
        await self.database.execute(query=query, values=_run_to_db(run))

    async def save_run(self, run):
        values = _run_to_db(run)
        uuid = values.pop("uuid")
        query = Runs.update().where(Runs.c.uuid == uuid).values(**values)
        await self.database.execute(query=query)

    async def get_run(self, run_id):
        query = Runs.select().where(Runs.c.uuid == run_id)
        row = await self.database.fetch_one(query=query)
        if row:
            return _db_to_run(row)

    async def get_runs(self, *, status=None, task_name=None, latest=None):
        query = sqlalchemy.select(
            [
                Runs.c.uuid,
                Runs.c.task,
                Runs.c.status,
                Runs.c.start,
                Runs.c.end,
                Runs.c.exit_code,
                Runs.c.run_info_json,
            ]
        )
        query = query.order_by(Runs.c.start.desc())
        if isinstance(status, Status):
            query = query.where(Runs.c.status == status.name)
        elif isinstance(status, list):
            query = query.where(Runs.c.status.in_(s.name for s in status))
        elif status:
            raise ValueError("status must be Status or list")
        if task_name:
            query = query.where(Runs.c.task == task_name)
        if latest:
            query = query.limit(latest)
        rows = await self.database.fetch_all(query=query)

        return [_db_to_run(r) for r in reversed(rows)]

    async def get_tasks(self):
        query = Tasks.select().order_by(Tasks.c.name.asc())
        rows = await self.database.fetch_all(query=query)
        return [_db_to_task(r) for r in rows]

    async def get_task(self, name):
        query = Tasks.select().where(Tasks.c.name == name)
        row = await self.database.fetch_one(query=query)
        if row:
            return _db_to_task(row)

    async def set_tasks(self, tasks):
        seen = set()
        for task in tasks:
            seen.add(task.name)
            dbtask = _task_to_db(task)

            query = Tasks.select().where(Tasks.c.name == task.name)
            res = await self.database.fetch_all(query=query)
            if res:
                query = Tasks.update().where(Tasks.c.name == task.name).values(**dbtask)
                res = await self.database.execute(query=query)
            else:
                query = Tasks.insert()
                await self.database.execute(query=query, values=dbtask)

        # delete the other tasks
        query = Tasks.delete().where(~Tasks.c.name.in_(seen))
        await self.database.execute(query)

    async def set_user(self, username, password, permissions):
        phash = hash_password(password)
        query = (
            Users.update()
            .where(Users.c.username == username)
            .values(password=phash, permissions=permissions or [])
        )
        res = await self.database.execute(query=query)
        if not res:
            query = Users.insert().values(
                username=username, password=phash, permissions=permissions or []
            )
            await self.database.execute(query=query)

    async def check_password(self, username, password):
        query = Users.select().where(Users.c.username == username)
        row = await self.database.fetch_one(query=query)
        if row:
            return verify_password(password, row["password"])

    async def get_users(self):
        query = Users.select()
        rows = await self.database.fetch_all(query=query)
        return [User(r["username"], r["password"], r["permissions"]) for r in rows]
