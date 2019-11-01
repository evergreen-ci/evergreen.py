from datetime import datetime, timedelta
import math
import time

import evergreen.util as under_test

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

SAMPLE_DATE_STRING = "2019-02-13T14:55:37.000Z"


class TestParseEvergreenDateTime(object):
    def test_float(self):
        now = datetime.now()
        timestamp = (time.mktime(now.timetuple()) + now.microsecond / 1000000.0)
        assert now == under_test.parse_evergreen_datetime(timestamp)

    def test_int(self):
        now = datetime.now()
        timestamp = int((time.mktime(now.timetuple()) + now.microsecond / 1000000.0))
        assert datetime.fromtimestamp(timestamp) == under_test.parse_evergreen_datetime(timestamp)

    def test_no_datetime(self):
        assert not under_test.parse_evergreen_datetime(None)

    def test_returns_a_datetime_object(self):
        now = datetime.now()
        now_str = now.strftime(under_test.EVG_DATETIME_FORMAT)

        assert now == under_test.parse_evergreen_datetime(now_str)


class TestFormatEvergreenDatetime(object):
    def test_date_is_formatted(self):
        now = datetime.now()

        now_str = under_test.format_evergreen_datetime(now)

        assert isinstance(now_str, str)


class TestParseEvergreenDate(object):
    def test_no_date(self):
        assert not under_test.parse_evergreen_date(None)

    def test_returns_a_date_object(self):
        now = datetime.now()
        now_str = now.strftime(under_test.EVG_DATE_FORMAT)

        assert now.date() == under_test.parse_evergreen_date(now_str)


def mock_by_seconds(start_time, n_items):
    return [MagicMock(the_time=(start_time - timedelta(minutes=7 * i))) for i in range(n_items)]


class TestIteratorByTimeWindow(object):
    def test_iter_ends_before_start_returns_nothing(self):
        now = datetime.now()
        iterator = mock_by_seconds(now, 5)
        start_time = now - timedelta(hours=1)
        end_time = start_time - timedelta(hours=1)

        items = list(under_test.iterate_by_time_window(iterator, start_time, end_time, "the_time"))
        assert not items

    def test_iter_ends_after_end_returns_nothing(self):
        now = datetime.now()
        start_time = now - timedelta(hours=1)
        end_time = start_time - timedelta(hours=1)
        iterator = mock_by_seconds(end_time - timedelta(minutes=5), 5)

        items = list(under_test.iterate_by_time_window(iterator, start_time, end_time, "the_time"))
        assert not items

    def test_items_in_window_are_returned(self):
        now = datetime.now()
        start_time = now - timedelta(hours=1)
        end_time = start_time - timedelta(hours=1)
        iterator = mock_by_seconds(now, 100)

        items = list(under_test.iterate_by_time_window(iterator, start_time, end_time, "the_time"))
        assert math.ceil(60 / 7) == len(items)
