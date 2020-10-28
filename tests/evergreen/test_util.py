import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import evergreen.util as under_test


class TestParseEvergreenDateTime(object):
    def test_float(self):
        now = datetime.now()
        timestamp = time.mktime(now.timetuple()) + now.microsecond / 1000000.0
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

        assert now == under_test.parse_evergreen_datetime(now_str).replace(tzinfo=None)

    def test_milliseconds_evergreen_format(self):
        assert isinstance(under_test.parse_evergreen_datetime("2019-02-13T14:55:37.000Z"), datetime)

    def test_no_milliseconds_evergreen_format(self):
        assert isinstance(under_test.parse_evergreen_datetime("2019-02-13T14:55:37Z"), datetime)


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


class TestFormatEvergreenDate(object):
    def test_date_is_formatted(self):
        now = datetime.now()

        now_str = under_test.format_evergreen_date(now)

        assert isinstance(now_str, str)


def mock_by_seconds(start_time, n_items):
    return [MagicMock(the_time=(start_time - timedelta(minutes=7 * i))) for i in range(n_items)]


class TestIteratorByTimeWindow(object):
    def test_iter_ends_before_start_returns_nothing(self):
        now = datetime.now()
        iterator = mock_by_seconds(now, 5)
        before_time = now - timedelta(hours=1)
        after_time = before_time - timedelta(hours=1)

        items = list(
            under_test.iterate_by_time_window(iterator, before_time, after_time, "the_time")
        )
        assert not items

    def test_iter_ends_after_end_returns_nothing(self):
        now = datetime.now()
        before_time = now - timedelta(hours=1)
        after_time = before_time - timedelta(hours=1)
        iterator = mock_by_seconds(after_time - timedelta(minutes=5), 5)

        items = list(
            under_test.iterate_by_time_window(iterator, before_time, after_time, "the_time")
        )
        assert not items

    def test_items_in_window_are_returned(self):
        now = datetime.now()
        before_time = now - timedelta(hours=1)
        after_time = before_time - timedelta(hours=1)
        iterator = mock_by_seconds(now, 100)

        items = list(
            under_test.iterate_by_time_window(iterator, before_time, after_time, "the_time")
        )
        assert (60 // 7) + 1 == len(items)
