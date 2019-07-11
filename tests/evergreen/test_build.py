# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/build.py."""
from __future__ import absolute_import

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from evergreen.build import Build
from evergreen.metrics.buildmetrics import BuildMetrics


class TestBuild(object):
    def test_basic_data(self, sample_build):
        build = Build(sample_build, None)
        assert sample_build['project_id'] == build.project_id

    def test_get_tasks(self, sample_build):
        mock_api = MagicMock()
        build = Build(sample_build, mock_api)
        assert mock_api.tasks_by_build.return_value == build.get_tasks()

    def test_status_counts(self, sample_build):
        build = Build(sample_build, None)
        assert sample_build['status_counts']['succeeded'] == build.status_counts.succeeded
        assert sample_build['status_counts']['failed'] == build.status_counts.failed
        assert sample_build['status_counts']['started'] == build.status_counts.started
        assert sample_build['status_counts']['timed_out'] == build.status_counts.timed_out

    def test_get_metrics_not_completed(self, sample_build):
        sample_build['status'] = 'created'
        build = Build(sample_build, None)

        assert not build.get_metrics()

    def test_get_metrics_completed(self, sample_build):
        sample_build['status'] = 'success'
        mock_api = MagicMock()
        build = Build(sample_build, mock_api)

        metrics = build.get_metrics()
        assert isinstance(metrics, BuildMetrics)
