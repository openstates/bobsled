import datetime
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, JSONAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection


class Status:
    Running = 'running'
    Frozen = 'frozen'
    Error = 'error'
    Success = 'success'


class StatusIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    status = UnicodeAttribute(hash_key=True)


class Run(Model):
    class Meta:
        table_name = "bobsled-run"
    job = UnicodeAttribute(hash_key=True)
    start = UTCDateTimeAttribute(range_key=True, default=datetime.datetime.utcnow)
    end = UTCDateTimeAttribute(null=True)
    task_definition = JSONAttribute()
    task_arn = UnicodeAttribute()
    status = UnicodeAttribute(default=Status.Running)
    status_index = StatusIndex()


def create_tables(delete=False):
    if delete:
        Run.delete_table()
    if not Run.exists():
        Run.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
