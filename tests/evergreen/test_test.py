# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/test.py."""
from __future__ import absolute_import

from evergreen.tst import Tst


class TestTest(object):
    def test_get_attributes(self, sample_test):
        test = Tst(sample_test, None)
        assert test.task_id == sample_test['task_id']
        assert test.exit_code == sample_test['exit_code']

    def test_logs(self, sample_test):
        test = Tst(sample_test, None)
        assert test.logs.url == sample_test['logs']['url']
