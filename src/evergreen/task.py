# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib

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


class Artifact(_BaseEvergreenObject):
    """Representation of a task artifact from evergreen."""

    name = evg_attrib('name')
    url = evg_attrib('url')
    visibility = evg_attrib('visibility')
    ignore_for_fetch = evg_attrib('ignore_for_fetch')

    def __init__(self, json, api):
        """Create an instance of an evergreen task artifact."""
        super(Artifact, self).__init__(json, api)


class StatusDetails(_BaseEvergreenObject):
    """Representation of a task status details from evergreen."""

    status = evg_attrib('status')
    type = evg_attrib('type')
    desc = evg_attrib('desc')
    timed_out = evg_attrib('timed_out')

    def __init__(self, json, api):
        """Create an instance of an evergreen task status details."""
        super(StatusDetails, self).__init__(json, api)


class Task(_BaseEvergreenObject):
    """Representation of an Evergreen task."""

    task_id = evg_attrib('task_id')
    project_id = evg_attrib('project_id')
    create_time = evg_datetime_attrib('create_time')
    dispatch_time = evg_datetime_attrib('dispatch_time')
    scheduled_time = evg_datetime_attrib('scheduled_time')
    start_time = evg_datetime_attrib('start_time')
    finish_time = evg_datetime_attrib('finish_time')
    ingest_time = evg_datetime_attrib('ingest_time')
    version_id = evg_attrib('version_id')
    revision = evg_attrib('revision')
    priority = evg_attrib('priority')
    activated = evg_attrib('activated')
    activated_by = evg_attrib('activated_by')
    build_id = evg_attrib('build_id')
    distro_id = evg_attrib('distro_id')
    build_variant = evg_attrib('build_variant')
    depends_on = evg_attrib('depends_on')
    display_name = evg_attrib('display_name')
    host_id = evg_attrib('host_id')
    restarts = evg_attrib('restarts')
    execution = evg_attrib('execution')
    order = evg_attrib('order')
    status = evg_attrib('status')
    time_taken_ms = evg_attrib('time_taken_ms')
    expected_duration_ms = evg_attrib('expected_duration_ms')
    est_wait_to_start_ms = evg_attrib('est_wait_to_start_ms')
    estimated_cost = evg_attrib('estimated_cost')
    generate_task = evg_attrib('generate_task')
    generated_by = evg_attrib('generated_by')
    display_only = evg_attrib('display_only')

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        super(Task, self).__init__(json, api)
        self._logs_map = None

    @property
    def artifacts(self):
        """
        Retrieve the artifacts for the given task.
        :return: List of artifacts.
        """
        return [Artifact(artifact, self._api) for artifact in self.json['artifacts']]

    @property
    def log_map(self):
        """
        Retrieve a dict of all the logs.
        :return: Dictionary of the logs.
        """
        if not self._logs_map:
            self._logs_map = {key: value for key, value in self.json['logs'].items()}
        return self._logs_map

    @property
    def status_details(self):
        """
        Retrieve the status details for the given task.
        :return: Status details.
        """
        return StatusDetails(self.json['status_details'], self._api)

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
        if not self.is_success() and self.status_details and self.status_details.type:
            return self.status_details.type == EVG_SYSTEM_FAILURE_STATUS
        return False

    def is_timeout(self):
        """
        Whether task results in a timeout.

        :return: True if task was a timeout.
        """
        if not self.is_success() and self.status_details and self.status_details.timed_out:
            return self.status_details.timed_out
        return False
