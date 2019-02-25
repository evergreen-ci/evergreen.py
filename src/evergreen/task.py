# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

EVG_SUCCESS_STATUS = 'success'
EVG_SYSTEM_FAILURE_STATUS = 'system'

_EVG_DATE_FIELDS_IN_TASK = frozenset([
    'create_time',
    'dispatch_time',
    'finish_time',
    'ingest_time',
    'scheduled_time',
    'start_time',
])


class Task(_BaseEvergreenObject):
    """Representation of an Evergreen task."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        super(Task, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_TASK

    def get_execution(self, execution):
        """
        Get the task info for the specified execution.

        :param execution: Index of execution.
        :return: Task info for specified execution.
        """
        if self.execution == execution:
            return self

        if 'previous_executions' in self.json:
            for task in self.json['previous_executions']:
                if task['execution'] == execution:
                    return Task(task, self._api)

        return None

    def wait_time(self):
        """
        Get the time taken until the task started running.

        :return: Time taken until task started running.
        """
        if self.start_time and self.ingest_time:
            return self.start_time - self.ingest_time
        return None

    def is_success(self):
        """
        Whether task was successful.

        :return: True if task was successful.
        """
        return self.status == EVG_SUCCESS_STATUS

    def is_system_failure(self):
        """
        Whether task resulted in a system failure.

        :return: True if task was a system failure.
        """
        if not self.is_success() and self.status_details and self.status_details['type']:
            return self.status_details['type'] == EVG_SYSTEM_FAILURE_STATUS
        return False

    def is_timeout(self):
        """
        Whether task results in a timeout.

        :return: True if task was a timeout.
        """
        if not self.is_success() and self.status_details and self.status_details['timed_out']:
            return self.status_details['timed_out']
        return False
