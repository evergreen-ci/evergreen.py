# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject


class Build(_BaseEvergreenObject):
    """Representation of an Evergreen build."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        super(Build, self).__init__(json, api)

    def get_tasks(self, fetch_all_executions=False):
        """
        Get all tasks for this build.

        :param fetch_all_executions:  fetch all executions for tasks.
        :return: List of all tasks.
        """
        return self._api.tasks_by_build(self._id, fetch_all_executions)
