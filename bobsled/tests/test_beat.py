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


def test_recurring_hours():
    assert next_cron("0 */2 * * ?", midnight) == datetime.datetime(2020, 1, 1, 2, 0)
    assert next_cron("0 */2 * * ?", noon) == datetime.datetime(2020, 1, 1, 14, 0)
    assert next_cron("0 */2 * * ?", ninepm) == datetime.datetime(2020, 1, 1, 22, 0)

    assert next_cron("0 */6 * * ?", midnight) == datetime.datetime(2020, 1, 1, 6, 0)
    assert next_cron("0 */6 * * ?", noon) == datetime.datetime(2020, 1, 1, 18, 0)
    assert next_cron("0 */6 * * ?", ninepm) == datetime.datetime(2020, 1, 2, 0, 0)


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


def test_monthly():
    # run on the first of the month
    assert next_cron(
        "0 0 1 * ?", datetime.datetime(2020, 1, 1, 0, 1)
    ) == datetime.datetime(2020, 2, 1, 0, 0)

    # run on the first and fifteenth of the month
    assert next_cron(
        "0 0 1,15 * ?", datetime.datetime(2020, 1, 1, 0, 1)
    ) == datetime.datetime(2020, 1, 15, 0, 0)

    # ensure that days of month don't matter
    assert next_cron(
        "0 0 1 * ?", datetime.datetime(2021, 2, 20, 0, 1)
    ) == datetime.datetime(2021, 3, 1, 0, 0)


def test_month_rollover():
    # going from april to may, the initial bug
    april30 = datetime.datetime(2020, 4, 30, 23, 0)
    assert next_cron("0 4 * * ?", april30) == datetime.datetime(2020, 5, 1, 4, 0)

    # going from feb to march, leap year check
    feb28 = datetime.datetime(2020, 2, 28, 23, 0)
    assert next_cron("0 4 * * ?", feb28) == datetime.datetime(2020, 2, 29, 4, 0)
    feb29 = datetime.datetime(2020, 2, 29, 23, 0)
    assert next_cron("0 4 * * ?", feb29) == datetime.datetime(2020, 3, 1, 4, 0)


def test_dec_jan_rollover():
    # going from dec to january
    dec = datetime.datetime(2020, 12, 31, 23, 0)
    assert next_cron("0 4 * * ?", dec) == datetime.datetime(2021, 1, 1, 4, 0)


def test_dow():
    wed = datetime.datetime(2021, 2, 24)  # a wednesday
    assert next_cron("0 4 * * 0", wed) == datetime.datetime(
        2021, 3, 1, 4, 0
    )  # the next monday

    wed = datetime.datetime(2021, 2, 24)  # a wednesday
    assert next_cron("0 4 * * 1,5", wed).weekday() == 5  # saturday
    wed = datetime.datetime(2021, 2, 28)  # a sunday
    assert next_cron("0 4 * * 1,5", wed).weekday() == 1  # tuesday
