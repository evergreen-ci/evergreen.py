# -*- encoding: utf-8 -*-
"""Unit tests for stats representation of evergreen."""
from __future__ import absolute_import

from evergreen.task_reliability import TaskReliability as tr


class TestTaskReliability(object):
    def test_get_attributes(self, sample_task_reliability):
        task_reliability = tr(sample_task_reliability, None)
        assert task_reliability.task_name == sample_task_reliability["task_name"]
        assert task_reliability.success_rate == sample_task_reliability["success_rate"]
