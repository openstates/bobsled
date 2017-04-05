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
    start = UTCDateTimeAttribute(range_key=True, default=datetime.datetime.utcnow)


class Run(Model):
    class Meta:
        table_name = "bobsled-run"
    job = UnicodeAttribute(hash_key=True)
    start = UTCDateTimeAttribute(range_key=True, default=datetime.datetime.utcnow)
    end = UTCDateTimeAttribute(null=True)
    task_definition = JSONAttribute()
    task_arn = UnicodeAttribute()
    status = UnicodeAttribute(default=Status.Running)

    # indices
    status_index = StatusIndex()

    @classmethod
    def recent(self, days, statuses=None):
        results = []
        if not statuses:
            statuses = [Status.Error, Status.Success]
        since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        for s in statuses:
            results.extend(Run.status_index.query(s, start__gt=since))
        return results


def create_tables():
    Run.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
