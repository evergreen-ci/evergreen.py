# -*- encoding: utf-8 -*-
"""Host representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject


class RunningTask(_BaseEvergreenObject):
    """Representation of a running task."""

    def __init__(self, json, api):
        """
        Create an instance of a Running Task.

        :param json: json of running task.
        :param api: Evergreen API.
        """
        super(RunningTask, self).__init__(json, api)

    def get_build(self):
        """
        Get build for the running task.

        :return: build object for task.
        """
        return self._api.build_by_id(self.build_id)

    def get_version(self):
        """
        Get version for the running task.

        :return: version object for task.
        """
        return self._api.version_by_id(self.version_id)


class Host(_BaseEvergreenObject):
    """Representation of an Evergreen host."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen host.
        """
        super(Host, self).__init__(json, api)

    @property
    def running_task(self):
        return RunningTask(self.json['running_task'], self._api)

    def get_build(self):
        """
        Get the build for the build using this host.

        :return: build for task running on this host.
        """
        return self.running_task.get_build()

    def get_version(self):
        """
        Get the version for the task using this host.

        :return: version for task running on this host.
        """
        return self.running_task.get_version()

    def __str__(self):
        return '{host_id}: {distro_id} - {status}'.format(
            host_id=self.host_id, distro_id=self.distro['distro_id'], status=self.status)
