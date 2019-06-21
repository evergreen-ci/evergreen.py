# -*- encoding: utf-8 -*-
"""Host representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib


class HostDistro(_BaseEvergreenObject):
    """Representation of a distro."""

    distro_id = evg_attrib('distro_id')
    provider = evg_attrib('provider')
    image_id = evg_attrib('image_id')

    def __init__(self, json, api):
        """
        Create an instance of a distro.

        :param json: json of distro.
        :param api: Evergreen API.
        """
        super(HostDistro, self).__init__(json, api)


class RunningTask(_BaseEvergreenObject):
    """Representation of a running task."""

    task_id = evg_attrib('task_id')
    name = evg_attrib('name')
    dispatch_time = evg_datetime_attrib('dispatch_time')
    version_id = evg_attrib('version_id')
    build_id = evg_attrib('build_id')

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

    host_id = evg_attrib('host_id')
    host_url = evg_attrib('host_url')
    provisioned = evg_attrib('provisioned')
    started_by = evg_attrib('started_by')
    host_type = evg_attrib('host_type')
    user = evg_attrib('user')
    status = evg_attrib('status')
    user_host = evg_attrib('user_host')

    def __init__(self, json, api):
        """
        Create an instance of an evergreen host.
        """
        super(Host, self).__init__(json, api)

    @property
    def running_task(self):
        return RunningTask(self.json['running_task'], self._api)

    @property
    def distro(self):
        return HostDistro(self.json['distro'], self._api)

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
            host_id=self.host_id, distro_id=self.distro.distro_id, status=self.status)
