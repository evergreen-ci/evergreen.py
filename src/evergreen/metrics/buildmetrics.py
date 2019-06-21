# -*- encoding: utf-8 -*-
"""Version representation of evergreen."""
from __future__ import absolute_import
from __future__ import division


class BuildMetrics(object):
    """Metrics about an evergreen build."""

    def __init__(self, build_id, api):
        """
        Create an instance of build metrics.

        :param build_id: Id of build to analyze.
        :param api: Evergreen API.
        """
        self._build_id = build_id
        self._api = api

        self.success_count = 0
        self.failure_count = 0
        self.undispatched_count = 0
        self.timed_out_count = 0
        self.system_failure_count = 0

        self.estimated_build_costs = 0
        self.total_processing_time = 0

        self.create_times = []
        self.start_times = []
        self.finish_times = []

    def calculate(self):
        """
        Calculate metrics for the given build.

        :returns: self.
        """
        task_list = self._api.tasks_by_build(self._build_id)
        for task in task_list:
            self._count_task(task)

        return self

    @property
    def total_tasks(self):
        """
        Get the total tasks in the build.
        :return: total tasks.
        """
        return self.success_count + self.failure_count + self.undispatched_count

    @property
    def pct_tasks_success(self):
        """
        Get the percentage of successful tasks.

        :return: Percentage of successful tasks.
        """
        return self._percent_tasks(self.success_count)

    def _percent_tasks(self, n_tasks):
        """
        Calculate the percent of n_tasks out of total.

        :param n_tasks: Number of tasks to calculate percent of.
        :return: percentage n_tasks is out of total tasks.
        """
        if self.total_tasks == 0:
            return 0
        return n_tasks / self.total_tasks

    def _count_task(self, task):
        """
        Add stats for the given task to the metrics.
        :param task: Task to add.
        """
        if task.is_undispatched():
            self.undispatched_count += 1
            return  # An 'undispatched' task has no useful stats.

        if task.is_success():
            self.success_count += 1
        else:
            self.failure_count += 1
            if task.is_system_failure():
                self.system_failure_count += 1
            if task.is_timeout():
                self.timed_out_count += 1

        if task.ingest_time:
            self.create_times.append(task.ingest_time)
        else:
            self.create_times.append(task.start_time)

        self.finish_times.append(task.finish_time)
        self.start_times.append(task.start_time)

        self.estimated_build_costs += task.estimated_cost
        self.total_processing_time += task.time_taken_ms / 1000
