# -*- encoding: utf-8 -*-
"""Host representation of evergreen."""
from __future__ import absolute_import


class RunningTask(object):
    """Representation of a running task."""

    def __init__(self, running_task_json, api):
        """
        Create an instance of a Running Task.

        :param running_task_json: json of running task.
        :param api: Evergreen API.
        """
        self.json = running_task_json
        self._api = api

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown running task attribute {0}'.format(item))

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


HOST_SUB_ATTRIBUTE_MAP = {
    'running_task': RunningTask,
}


class Host(object):
    """Representation of an Evergreen host."""

    def __init__(self, host_json, api):
        """
        Create an instance of an evergreen host.
        """
        self.json = host_json
        self._api = api

    def __getattr__(self, item):
        if item in self.json:
            if item in HOST_SUB_ATTRIBUTE_MAP:
                return HOST_SUB_ATTRIBUTE_MAP[item](self.json(item))
            return self.json[item]
        raise TypeError('Unknown host attribute {0}'.format(item))

    def get_build(self):
        """
        Get the build for the build using this host.

        :return: build for task running on this host.
        """
        return self.running_task.get_build()

    def __str__(self):
        return '{host_id}: {distro_id} - {status}'.format(
            host_id=self.host_id,
            distro_id=self.distro['distro_id'],
            status=self.status
        )
