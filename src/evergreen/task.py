# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib

EVG_SUCCESS_STATUS = 'success'
EVG_SYSTEM_FAILURE_STATUS = 'system'
EVG_UNDISPATCHED_STATUS = 'undispatched'

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

    activated = evg_attrib('activated')
    activated_by = evg_attrib('activated_by')
    build_id = evg_attrib('build_id')
    build_variant = evg_attrib('build_variant')
    create_time = evg_datetime_attrib('create_time')
    depends_on = evg_attrib('depends_on')
    dispatch_time = evg_datetime_attrib('dispatch_time')
    display_name = evg_attrib('display_name')
    display_only = evg_attrib('display_only')
    distro_id = evg_attrib('distro_id')
    est_wait_to_start_ms = evg_attrib('est_wait_to_start_ms')
    estimated_cost = evg_attrib('estimated_cost')
    execution = evg_attrib('execution')
    expected_duration_ms = evg_attrib('expected_duration_ms')
    finish_time = evg_datetime_attrib('finish_time')
    generate_task = evg_attrib('generate_task')
    generated_by = evg_attrib('generated_by')
    host_id = evg_attrib('host_id')
    ingest_time = evg_datetime_attrib('ingest_time')
    mainline = evg_attrib('mainline')
    order = evg_attrib('order')
    project_id = evg_attrib('project_id')
    priority = evg_attrib('priority')
    restarts = evg_attrib('restarts')
    revision = evg_attrib('revision')
    scheduled_time = evg_datetime_attrib('scheduled_time')
    start_time = evg_datetime_attrib('start_time')
    status = evg_attrib('status')
    task_group = evg_attrib('task_group')
    task_group_max_hosts = evg_attrib('task_group_max_hosts')
    task_id = evg_attrib('task_id')
    time_taken_ms = evg_attrib('time_taken_ms')
    version_id = evg_attrib('version_id')

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

    def retrieve_log(self, log_name, raw=False):
        """
        Retrieve the contents of the specified log.

        :param log_name: Name of log to retrieve.
        :param raw: Retrieve raw version of log.
        :return: Contents of the specified log.
        """
        return self._api.retrieve_task_log(self.log_map[log_name], raw)

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

    def wait_time_once_unblocked(self):
        """
        Get the time taken until the task started running
        once it is unblocked by task dependencies.

        :return: Time taken until task started running.
        """
        if self.start_time and self.scheduled_time:
            return self.start_time - self.scheduled_time
        return None

    def is_success(self):
        """
        Whether task was successful.

        :return: True if task was successful.
        """
        return self.status == EVG_SUCCESS_STATUS

    def is_undispatched(self):
        """
        Whether the task was undispatched.

        :return: True is task was undispatched.
        """
        return self.status == EVG_UNDISPATCHED_STATUS

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

    def is_active(self):
        """
        Determine if the given task is active.

        :return: True if task is active.
        """
        return self.scheduled_time and not self.finish_time
