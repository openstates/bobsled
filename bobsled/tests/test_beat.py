import datetime
from ..beat import next_cron

midnight = datetime.datetime(2020, 1, 1, 0, 0)
noon = datetime.datetime(2020, 1, 1, 12, 0)
ninepm = datetime.datetime(2020, 1, 1, 21, 0)


def test_simple():
    assert next_cron("0 4 * * ?", midnight) == datetime.datetime(2020, 1, 1, 4, 0)
    assert next_cron("0 4 * * ?", noon) == datetime.datetime(2020, 1, 2, 4, 0)


def test_multiple_hours():
    assert next_cron("0 4,16 * * ?", midnight) == datetime.datetime(2020, 1, 1, 4, 0)
    assert next_cron("0 4,16 * * ?", noon) == datetime.datetime(2020, 1, 1, 16, 0)
    assert next_cron("0 4,16 * * ?", ninepm) == datetime.datetime(2020, 1, 2, 4, 0)


def test_hour_range():
    assert next_cron("0 11-13 * * ?", midnight) == datetime.datetime(2020, 1, 1, 11, 0)
    assert next_cron("0 11-13 * * ?", noon) == datetime.datetime(2020, 1, 1, 13, 0)
    assert next_cron("0 11-13 * * ?", ninepm) == datetime.datetime(2020, 1, 2, 11, 0)


def test_next_minute():
    assert next_cron(
        "0,2,4 * * * ?", datetime.datetime(2020, 1, 1, 0, 1)
    ) == datetime.datetime(2020, 1, 1, 0, 2)
    assert next_cron(
        "0,2,4 * * * ?", datetime.datetime(2020, 1, 1, 0, 2)
    ) == datetime.datetime(2020, 1, 1, 0, 4)
    assert next_cron(
        "0,2,4 * * * ?", datetime.datetime(2020, 1, 1, 0, 5)
    ) == datetime.datetime(2020, 1, 1, 1, 0)
