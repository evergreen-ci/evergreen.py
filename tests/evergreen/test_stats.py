# -*- encoding: utf-8 -*-
"""Unit tests for stats representation of evergreen."""
from __future__ import absolute_import

from evergreen.stats import TestStats as ts


class TestTestStats(object):
    def test_get_attributes(self, sample_test_stats):
        test_stats = ts(sample_test_stats, None)
        assert test_stats.test_file == sample_test_stats['test_file']
        assert test_stats.task_name == sample_test_stats['task_name']
