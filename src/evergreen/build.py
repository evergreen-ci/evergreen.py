# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib


class StatusCounts(_BaseEvergreenObject):
    """Representation of Evergreen StatusCounts."""

    succeeded = evg_attrib('succeeded')
    failed = evg_attrib('failed')
    started = evg_attrib('started')
    undispatched = evg_attrib('undispatched')
    inactivate = evg_attrib('inactive')
    dispatched = evg_attrib('dispatched')
    timed_out = evg_attrib('timed_out')

    def __init__(self, json, api):
        super(StatusCounts, self).__init__(json, api)


class Build(_BaseEvergreenObject):
    """Representation of an Evergreen build."""

    id = evg_attrib('_id')
    project_id = evg_attrib('project_id')
    create_time = evg_datetime_attrib('create_time')
    start_time = evg_datetime_attrib('start_time')
    finish_time = evg_datetime_attrib('finish_time')
    version = evg_attrib('version')
    branch = evg_attrib('branch')
    git_hash = evg_attrib('git_hash')
    build_variant = evg_attrib('build_variant')
    status = evg_attrib('status')
    activated = evg_attrib('status')
    activated_by = evg_attrib('activated_by')
    activated_time = evg_datetime_attrib('activated_time')
    order = evg_attrib('order')
    tasks = evg_attrib('tasks')
    time_taken_ms = evg_attrib('time_taken_ms')
    display_name = evg_attrib('display_name')
    predicted_makespan_ms = evg_attrib('predicted_makespan_ms')
    actual_makespan_ms = evg_attrib('actual_makespan_ms')
    origin = evg_attrib('origin')

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        super(Build, self).__init__(json, api)

    @property
    def status_counts(self):
        return StatusCounts(self.json['status_counts'], self._api)

    def get_tasks(self, fetch_all_executions=False):
        """
        Get all tasks for this build.

        :param fetch_all_executions:  fetch all executions for tasks.
        :return: List of all tasks.
        """
        return self._api.tasks_by_build(self._id, fetch_all_executions)
