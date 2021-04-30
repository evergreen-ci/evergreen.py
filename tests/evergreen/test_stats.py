# -*- encoding: utf-8 -*-
"""Unit tests for stats representation of evergreen."""
from __future__ import absolute_import

from evergreen.stats import TaskStats, TestStats


class TestTestStats(object):
    def test_get_attributes(self, sample_test_stats):
        test_stats = TestStats(sample_test_stats, None)
        assert test_stats.test_file == sample_test_stats["test_file"]
        assert test_stats.task_name == sample_test_stats["task_name"]


class TestTaskStats(object):
    def test_get_attributes(self, sample_task_stats):
        task_stats = TaskStats(sample_task_stats, None)
        assert task_stats.test_file == sample_task_stats["test_file"]
        assert task_stats.task_name == sample_task_stats["task_name"]
        assert task_stats.num_fail == sample_task_stats["num_failed"]
        assert task_stats.num_pass == sample_task_stats["num_success"]
        assert task_stats.avg_duration_pass == sample_task_stats["avg_duration_success"]
