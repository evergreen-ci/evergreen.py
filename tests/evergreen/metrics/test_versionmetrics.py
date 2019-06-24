# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/metrics/versionmetrics.py."""
from __future__ import absolute_import

from datetime import datetime, timedelta

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import evergreen.metrics.versionmetrics as under_test


def mock_build_metrics(success_count=0, cost=0):
    now = datetime.now()
    build_metrics = MagicMock()
    build_metrics.total_processing_time = 0
    build_metrics.success_count = success_count
    build_metrics.failure_count = 0
    build_metrics.timed_out_count = 0
    build_metrics.system_failure_count = 0
    build_metrics.estimated_build_costs = cost
    build_metrics.create_time = now
    build_metrics.start_time = now + timedelta(minutes=30)
    build_metrics.end_time = now + timedelta(minutes=60)

    return build_metrics


def create_mock_build(bm_list=None):
    mock_build = MagicMock()
    mock_build.get_metrics.return_value = bm_list
    return mock_build


def create_mock_build_list(n, bm_list=None):
    return [create_mock_build(bm_list) for _ in range(n)]


def create_mock_version(builds=None):
    mock_version = MagicMock(version_id='version_id')
    mock_version.get_builds.return_value = builds if builds else []
    return mock_version


class TestVersionMetrics(object):
    def test_with_no_builds(self):
        mock_version = create_mock_version()
        version_metrics = under_test.VersionMetrics(mock_version).calculate()

        assert version_metrics.total_processing_time == 0
        assert version_metrics.task_success_count == 0
        assert version_metrics.estimated_cost == 0

        assert not version_metrics.create_time
        assert not version_metrics.start_time
        assert not version_metrics.end_time
        assert not version_metrics.makespan
        assert not version_metrics.wait_time

    def test_multiple_builds(self, sample_task, sample_build):
        n_tasks = 5
        n_builds = 3
        mock_build_metric = mock_build_metrics(n_tasks, sample_task['estimated_cost'] * n_tasks)
        build_list = create_mock_build_list(n_builds, mock_build_metric)
        mock_version = create_mock_version(build_list)

        version_metrics = under_test.VersionMetrics(mock_version).calculate()

        total_tasks = n_tasks * n_builds
        assert version_metrics.task_success_count == total_tasks
        assert version_metrics.task_failure_count == 0
        assert version_metrics.estimated_cost == total_tasks * sample_task['estimated_cost']
        assert version_metrics.pct_tasks_success == 1
        assert version_metrics.pct_tasks_failure == 0
        assert version_metrics.pct_tasks_system_failure == 0
        assert version_metrics.pct_tasks_timeout == 0

    def test_add_success_build(self):
        build_metrics = mock_build_metrics()
        build_metrics.success_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert version_metrics.task_success_count == build_metrics.success_count
        assert version_metrics.task_failure_count == 0
        assert version_metrics.task_system_failure_count == 0
        assert version_metrics.task_timeout_count == 0

    def test_add_failed_build(self):
        build_metrics = mock_build_metrics()
        build_metrics.failure_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert version_metrics.task_success_count == 0
        assert version_metrics.task_failure_count == build_metrics.failure_count
        assert version_metrics.task_system_failure_count == 0
        assert version_metrics.task_timeout_count == 0

    def test_add_timeout_build(self):
        build_metrics = mock_build_metrics()
        build_metrics.timed_out_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert version_metrics.task_success_count == 0
        assert version_metrics.task_failure_count == 0
        assert version_metrics.task_system_failure_count == 0
        assert version_metrics.task_timeout_count == build_metrics.timed_out_count

    def test_add_system_failure_build(self):
        build_metrics = mock_build_metrics()
        build_metrics.system_failure_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert version_metrics.task_success_count == 0
        assert version_metrics.task_failure_count == 0
        assert version_metrics.task_system_failure_count == build_metrics.system_failure_count
        assert version_metrics.task_timeout_count == 0

    def test_dict_format(self, sample_task):
        build_metrics = mock_build_metrics()
        build_metrics.system_failure_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        ver_dict = version_metrics.as_dict()
        assert ver_dict['version'] == mock_version.version_id
        assert 'build_metrics' not in ver_dict

    def test_dict_format_with_children(self):
        build_metrics = mock_build_metrics()
        build_metrics.system_failure_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        ver_dict = version_metrics.as_dict(include_children=True)
        assert ver_dict['version'] == mock_version.version_id
        assert len(ver_dict['build_metrics']) == 1
        assert ver_dict['build_metrics'][0] == build_metrics.as_dict.return_value

    def test_string_format(self):
        build_metrics = mock_build_metrics()
        build_metrics.system_failure_count = 5
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert mock_version.version_id in str(version_metrics)

    def test_no_time(self):
        build_metrics = mock_build_metrics()
        build_metrics.create_time = None
        build_metrics.start_time = None
        build_metrics.end_time = None
        build_mock = MagicMock()
        build_mock.get_metrics.return_value = build_metrics
        mock_version = create_mock_version()

        version_metrics = under_test.VersionMetrics(mock_version)
        version_metrics._count_build(build_mock)

        assert not version_metrics.create_time
        assert not version_metrics.start_time
        assert not version_metrics.end_time
        assert mock_version.version_id in str(version_metrics)


class TestPercentTasks(object):
    def test_percent_of_zero_tasks_is_zero(self):
        mock_version = create_mock_version()
        build_metrics = under_test.VersionMetrics(mock_version)

        assert build_metrics._percent_tasks(5) == 0

    def test_percent_of_non_zero_works(self):
        mock_version = create_mock_version()
        build_metrics = under_test.VersionMetrics(mock_version)
        build_metrics.task_success_count = 10

        assert build_metrics._percent_tasks(5) == 0.5
