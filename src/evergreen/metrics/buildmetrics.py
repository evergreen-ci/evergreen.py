# -*- encoding: utf-8 -*-
"""Metrics for Evergreen builds."""
from __future__ import absolute_import
from __future__ import division

from structlog import get_logger

from evergreen.errors.exceptions import ActiveTaskMetricsException

LOGGER = get_logger(__name__)


class BuildMetrics(object):
    """Metrics about an evergreen build."""

    def __init__(self, build):
        """
        Create an instance of build metrics.

        :param build: Build to analyze.
        """
        self.build = build

        self.success_count = 0
        self.failure_count = 0
        self.undispatched_count = 0
        self.timed_out_count = 0
        self.system_failure_count = 0

        self.estimated_build_costs = 0
        self.total_processing_time = 0

        self._create_times = []
        self._start_times = []
        self._finish_times = []

        self.task_list = None

    def calculate(self, task_filter_fn=None):
        """
        Calculate metrics for the given build.

        :param task_filter_fn: function to filter tasks included for metrics, should accept a task
                               argument.
        :returns: self.
        """
        all_tasks = self.build.get_tasks()
        filtered_task_list = all_tasks
        if task_filter_fn:
            filtered_task_list = [task for task in filtered_task_list if task_filter_fn(task)]

        self.task_list = filtered_task_list

        # We want to track display tasks, but not use them for metrics since they are just
        # containers to other tasks.
        filtered_task_list = [task for task in self.task_list if not task.display_only]
        for task in filtered_task_list:
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

    @property
    def pct_tasks_undispatched(self):
        """
        Get the percentage of undispatched tasks.

        :return: Percentage of undispatched tasks.
        """
        return self._percent_tasks(self.undispatched_count)

    @property
    def pct_tasks_failed(self):
        """
        Get the percentage of failed tasks.

        :return: Percentage of failed tasks.
        """
        return self._percent_tasks(self.failure_count)

    @property
    def pct_tasks_timed_out(self):
        """
        Get the percentage of timeout tasks.

        :return: Percentage of timeout tasks.
        """
        return self._percent_tasks(self.timed_out_count)

    @property
    def pct_tasks_system_failure(self):
        """
        Get the percentage of system failure tasks.

        :return: Percentage of system failure tasks.
        """
        return self._percent_tasks(self.system_failure_count)

    @property
    def create_time(self):
        """
        Time the first task of the build was created.

        :return: Time first task was created.
        """
        if self._create_times:
            return min(self._create_times)
        return None

    @property
    def start_time(self):
        """
        Time first task of build was started.

        :return: Time first task was started.
        """
        if self._start_times:
            return min(self._start_times)
        return None

    @property
    def end_time(self):
        """
        Time last task of build was completed.

        :return: Time last task was completed.
        """
        if self._finish_times:
            return max(self._finish_times)
        return None

    @property
    def makespan(self):
        """
        Wall clock duration of build.

        :return: Timedelta duration of build.
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def wait_time(self):
        """
        Wall clock duration until build was started.

        :return: Timedelta duration until build was started.
        """
        if self.start_time and self.create_time:
            return self.start_time - self.create_time
        return None

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

        if task.is_active():
            LOGGER.warning('Active task found during metrics collection', task_id=task.task_id)
            raise ActiveTaskMetricsException(task, 'Task in progress during metrics collection')

        if task.is_success():
            self.success_count += 1
        else:
            self.failure_count += 1
            if task.is_system_failure():
                self.system_failure_count += 1
            if task.is_timeout():
                self.timed_out_count += 1

        if task.ingest_time:
            self._create_times.append(task.ingest_time)
        else:
            self._create_times.append(task.start_time)

        if task.start_time:
            self._finish_times.append(task.finish_time)

        if task.start_time:
            self._start_times.append(task.start_time)

        self.estimated_build_costs += task.estimated_cost
        self.total_processing_time += task.time_taken_ms / 1000

    def as_dict(self, include_children=False):
        """
        Provide a dictionary representation.

        :param include_children: Include child tasks in dictionary.
        :return: Dictionary of metrics.
        """
        metric = {
            'build': self.build.id,
            'total_processing_time': self.total_processing_time,
            'makespan': self.makespan.total_seconds(),
            'wait_time': self.wait_time.total_seconds(),
            'total_tasks': self.total_tasks,
            'success_count': self.success_count,
            'pct_tasks_success': self.pct_tasks_success,
            'undispatched_count': self.undispatched_count,
            'pct_tasks_undispatched': self.pct_tasks_undispatched,
            'failure_count': self.failure_count,
            'pct_tasks_failed': self.pct_tasks_failed,
            'timed_out_count': self.timed_out_count,
            'system_failure_count': self.system_failure_count,
            'estimated_build_costs': self.estimated_build_costs,
        }

        if include_children:
            metric['tasks'] = [task.json for task in self.task_list]

        return metric

    def __str__(self):
        """
        Create string version of metrics.

        :return: String version of the metrics.
        """
        return """Build Id: {build_id}
        Total Processing Time: {total_processing_time:.2f}s ({total_processing_time_min:.2f}m)
        Makespan: {makespan:.2f}s ({makespan_min:.2f}m)
        Wait Time: {waittime:.2f}s ({waittime_min:.2f}m)
        Total Tasks: {total_tasks}
        Successful Tasks: {success_count} ({success_pct:.2%})
        Undispatched Tasks: {undispatched_count} ({undispatched_pct:.2%})
        Failed Tasks: {failed_count} ({failed_pct:.2%})
        Timeout Tasks: {timeout_count} ({timeout_pct:.2%})
        System Failure Tasks: {system_failure_count} ({system_failure_pct:.2%})
        Estimated Build Costs: {est_build_costs:.3f}
        """.format(
            build_id=self.build.id,
            total_processing_time=self.total_processing_time,
            total_processing_time_min=(self.total_processing_time / 60),
            makespan=(self.makespan.total_seconds()),
            makespan_min=(self.makespan.total_seconds() / 60),
            waittime=(self.wait_time.total_seconds()),
            waittime_min=(self.wait_time.total_seconds() / 60),
            total_tasks=self.total_tasks,
            success_count=self.success_count,
            success_pct=self.pct_tasks_success,
            undispatched_count=self.undispatched_count,
            undispatched_pct=self.pct_tasks_undispatched,
            failed_count=self.failure_count,
            failed_pct=self.pct_tasks_failed,
            timeout_count=self.timed_out_count,
            timeout_pct=self.pct_tasks_timed_out,
            system_failure_count=self.system_failure_count,
            system_failure_pct=self.pct_tasks_system_failure,
            est_build_costs=self.estimated_build_costs
        ).rstrip()
