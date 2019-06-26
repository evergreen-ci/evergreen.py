# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/metrics/buildmetrics.py."""
from __future__ import absolute_import

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import pytest

from evergreen.task import Task
from evergreen.errors.exceptions import ActiveTaskMetricsException

import evergreen.metrics.buildmetrics as under_test


def create_mock_build(task_list=None):
    mock_build = MagicMock(id="build_id")
    mock_build.get_tasks.return_value = task_list if task_list else []
    return mock_build


class TestBuildMetrics(object):
    def test_build_metrics_empty_for_no_builds(self):
        mock_build = create_mock_build()
        build_metrics = under_test.BuildMetrics(mock_build).calculate()

        assert build_metrics.total_tasks == 0
        assert build_metrics.total_processing_time == 0
        assert build_metrics.estimated_build_costs == 0
        assert build_metrics.pct_tasks_undispatched == 0
        assert build_metrics.pct_tasks_failed == 0
        assert build_metrics.pct_tasks_timed_out == 0
        assert build_metrics.pct_tasks_success == 0

        assert not build_metrics.create_time
        assert not build_metrics.start_time
        assert not build_metrics.end_time
        assert not build_metrics.makespan
        assert not build_metrics.wait_time

    def test_various_tasks(self, sample_task):
        n_tasks = 5
        task_list = [Task(sample_task, None) for _ in range(n_tasks)]
        mock_build = create_mock_build(task_list)

        build_metrics = under_test.BuildMetrics(mock_build).calculate()

        assert build_metrics.total_tasks == n_tasks
        assert build_metrics.pct_tasks_success == 1
        assert len(build_metrics._create_times) == n_tasks
        assert len(build_metrics._start_times) == n_tasks
        assert len(build_metrics._finish_times) == n_tasks

    def test_adding_successful_task(self, sample_task):
        sample_task['status'] = 'success'
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics._start_times) == 1
        assert build_metrics.failure_count == 0
        assert build_metrics.success_count == 1
        assert build_metrics.pct_tasks_success == 1
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0

    def test_adding_undispatched_task(self, sample_task):
        sample_task['status'] = 'undispatched'
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 1
        assert build_metrics.pct_tasks_undispatched == 1
        assert build_metrics.total_tasks == 1
        assert len(build_metrics._start_times) == 0

    def test_adding_failed_task(self, sample_task):
        sample_task['status'] = 'failed'
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics._start_times) == 1
        assert build_metrics.failure_count == 1
        assert build_metrics.pct_tasks_failed == 1
        assert build_metrics.success_count == 0
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0

    def test_adding_system_failed_task(self, sample_task):
        sample_task['status'] = 'failed'
        sample_task['status_details']['type'] = 'system'
        sample_task['status_details']['timed_out'] = True
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics._start_times) == 1
        assert build_metrics.failure_count == 1
        assert build_metrics.system_failure_count == 1
        assert build_metrics.pct_tasks_system_failure == 1
        assert build_metrics.timed_out_count == 1
        assert build_metrics.success_count == 0

    def test_adding_task_without_ingest_time(self, sample_task):
        del sample_task['ingest_time']
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert build_metrics.undispatched_count == 0
        assert build_metrics.total_tasks == 1
        assert len(build_metrics._start_times) == 1
        assert build_metrics.failure_count == 0
        assert build_metrics.success_count == 1
        assert build_metrics.system_failure_count == 0
        assert build_metrics.timed_out_count == 0

    def test_dict_format(self, sample_task):
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        bm_dict = build_metrics.as_dict()
        assert bm_dict['build'] == mock_build.id
        assert 'tasks' not in bm_dict

    def test_dict_format_with_children(self, sample_task):
        task = Task(sample_task, None)
        mock_build = create_mock_build([task])

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics.calculate()

        bm_dict = build_metrics.as_dict(include_children=True)
        assert bm_dict['build'] == mock_build.id
        assert len(bm_dict['tasks']) == 1
        assert bm_dict['tasks'][0]['task_id'] == task.task_id

    def test_string_format(self, sample_task):
        task = Task(sample_task, None)
        mock_build = create_mock_build([task])

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics._count_task(task)

        assert mock_build.id in str(build_metrics)

    def test_display_tasks_are_filtered(self, sample_task):
        sample_task['display_only'] = True
        task = Task(sample_task, None)
        mock_build = create_mock_build([task])

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics.calculate()

        assert len(build_metrics.task_list) == 1
        assert build_metrics.total_tasks == 0

    def test_task_filter(self, sample_task):
        n_tasks = 5
        task_list = [Task(sample_task, None) for _ in range(n_tasks)]
        sample_task_2 = sample_task.copy()
        filter_task_name = 'filter me'
        sample_task_2['display_name'] = filter_task_name
        task_list_2 = [Task(sample_task_2, None) for _ in range(n_tasks)]
        mock_build = create_mock_build(task_list + task_list_2)

        build_metrics = under_test.BuildMetrics(mock_build)
        build_metrics.calculate(lambda t: filter_task_name not in t.display_name)
        assert build_metrics.total_tasks == n_tasks

    def test_in_progress_task(self, sample_task):
        sample_task['finish_time'] = None
        task = Task(sample_task, None)
        mock_build = create_mock_build()

        build_metrics = under_test.BuildMetrics(mock_build)
        with pytest.raises(ActiveTaskMetricsException):
            build_metrics._count_task(task)


class TestPercentTasks(object):
    def test_percent_of_zero_tasks_is_zero(self):
        build_metrics = under_test.BuildMetrics('build')

        assert build_metrics._percent_tasks(5) == 0

    def test_percent_of_non_zero_works(self):
        build_metrics = under_test.BuildMetrics('build')
        build_metrics.success_count = 10

        assert build_metrics._percent_tasks(5) == 0.5
