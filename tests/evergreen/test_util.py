from datetime import datetime

import evergreen.util as under_test

SAMPLE_DATE_STRING = "2019-02-13T14:55:37.000Z"


class TestParseEvergreenDateTime(object):
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
