# -*- encoding: utf-8 -*-
"""Metrics for an evergreen version."""
from __future__ import absolute_import
from __future__ import division


class VersionMetrics(object):
    """Metrics about an evergreen version."""

    def __init__(self, version_id, api):
        """
        Create an instance of version metrics.

        :param version_id: Id of version to analyze.
        :param api: Evergreen API.
        """
        self._version_id = version_id
        self._api = api

        self.total_processing_time = 0
        self.task_success_count = 0
        self.task_failure_count = 0
        self.task_timeout_count = 0
        self.task_system_failure_count = 0
        self.estimated_cost = 0

    def calculate(self):
        """
        Calculate metrics for the given build.

        :returns: self.
        """
        build_list = self._api.builds_by_version(self._version_id)
        for build in build_list:
            self._count_build(build)

        return self

    @property
    def total_tasks(self):
        """
        Get the total tasks in the version.

        :return: total tasks
        """
        return self.task_success_count + self.task_failure_count

    @property
    def pct_tasks_success(self):
        """
        Get the percentage of successful tasks.
        :return: Percentage of successful tasks.
        """
        return self._percent_tasks(self.task_success_count)

    @property
    def pct_tasks_failure(self):
        """
        Get the percentage of failure tasks.
        :return: Percentage of failure tasks.
        """
        return self._percent_tasks(self.task_failure_count)

    @property
    def pct_tasks_timeout(self):
        """
        Get the percentage of timeout tasks.
        :return: Percentage of timeout tasks.
        """
        return self._percent_tasks(self.task_timeout_count)

    @property
    def pct_tasks_system_failure(self):
        """
        Get the percentage of system failure tasks.
        :return: Percentage of system failure tasks.
        """
        return self._percent_tasks(self.task_system_failure_count)

    def _percent_tasks(self, n_tasks):
        """
        Calculate the percent of n_tasks out of total.

        :param n_tasks: Number of tasks to calculate percent of.
        :return: percentage n_tasks is out of total tasks.
        """
        if self.total_tasks == 0:
            return 0

        return n_tasks / self.total_tasks

    def _count_build(self, build):
        """
        Add stats for the given build to the metrics.

        :param build: Build to add.
        """
        build_metrics = build.get_metrics()

        self.total_processing_time += build_metrics.total_processing_time
        self.task_success_count += build_metrics.success_count
        self.task_failure_count += build_metrics.failure_count
        self.task_timeout_count += build_metrics.timed_out_count
        self.task_system_failure_count += build_metrics.system_failure_count
        self.estimated_cost += build_metrics.estimated_build_costs
