# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/metrics/buildmetrics.py."""
from __future__ import absolute_import

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from evergreen.task import Task

import evergreen.metrics.buildmetrics as under_test


class TestBuildMetrics(object):
    def test_build_metrics_empty_for_no_builds(self):
        mock_api = MagicMock(tasks_by_build=lambda _: [])
        build_metrics = under_test.BuildMetrics('build_id', mock_api).calculate()

        assert build_metrics.total_tasks == 0
        assert build_metrics.total_processing_time == 0
        assert build_metrics.estimated_build_costs == 0

    def test_various_tasks(self, sample_task):
        n_tasks = 5
        task_list = [Task(sample_task, None) for _ in range(n_tasks)]
        mock_api = MagicMock(tasks_by_build=lambda _: task_list)
        build_metrics = under_test.BuildMetrics('build_id', mock_api).calculate()

        assert build_metrics.total_tasks == n_tasks
        assert build_metrics.pct_tasks_success == 1
        assert len(build_metrics.create_times) == n_tasks
        assert len(build_metrics.start_times) == n_tasks
        assert len(build_metrics.finish_times) == n_tasks

    def test_adding_successful_task(self, sample_task):
        sample_task['status'] = 'success'
        task = Task(sample_task, None)
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics.start_times) == 1
        assert build_metrics.failure_count == 0
        assert build_metrics.success_count == 1
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0

    def test_adding_undispatched_task(self, sample_task):
        sample_task['status'] = 'undispatched'
        task = Task(sample_task, None)
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 1
        assert build_metrics.total_tasks == 1
        assert len(build_metrics.start_times) == 0

    def test_adding_failed_task(self, sample_task):
        sample_task['status'] = 'failed'
        task = Task(sample_task, None)
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics.start_times) == 1
        assert build_metrics.failure_count == 1
        assert build_metrics.success_count == 0
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0

    def test_adding_system_failed_task(self, sample_task):
        sample_task['status'] = 'failed'
        sample_task['status_details']['type'] = 'system'
        sample_task['status_details']['timed_out'] = True
        task = Task(sample_task, None)
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics.start_times) == 1
        assert build_metrics.failure_count == 1
        assert build_metrics.system_failure_count == 1
        assert build_metrics.timed_out_count == 1
        assert build_metrics.success_count == 0

    def test_adding_task_without_ingest_time(self, sample_task):
        del sample_task['ingest_time']
        task = Task(sample_task, None)
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics.start_times) == 1
        assert build_metrics.failure_count == 0
        assert build_metrics.success_count == 1
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0


class TestPercentTasks(object):
    def test_percent_of_zero_tasks_is_zero(self):
        build_metrics = under_test.BuildMetrics('build_id', None)

        assert build_metrics._percent_tasks(5) == 0

    def test_percent_of_non_zero_works(self):
        build_metrics = under_test.BuildMetrics('build_id', None)
        build_metrics.success_count = 10

        assert build_metrics._percent_tasks(5) == 0.5
