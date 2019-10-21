# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/test.py."""
from __future__ import absolute_import

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock, patch

from evergreen.tst import Tst


class TestTest(object):
    def test_get_attributes(self, sample_test):
        test = Tst(sample_test, None)
        assert test.task_id == sample_test['task_id']
        assert test.exit_code == sample_test['exit_code']

    def test_logs(self, sample_test):
        test = Tst(sample_test, None)
        assert test.logs.url == sample_test['logs']['url']

    def test_log_stream(self, sample_test):
        mocked_api = MagicMock()
        test = Tst(sample_test, mocked_api)
        stream = test.logs.stream()

        mocked_api.stream_log.assert_called_with(sample_test['logs']['url_raw'])
        assert stream == mocked_api.stream_log.return_value
