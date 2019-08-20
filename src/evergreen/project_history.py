# -*- encoding: utf-8 -*-
"""Project history representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib


class ProjectHistoryTask(_BaseEvergreenObject):
    """
    Representation of a project history task in evergreen.
    """
    task_id = evg_attrib('task_id')
    status = evg_attrib('status')
    time_taken = evg_attrib('time_taken')

    def __init__(self, name, json, api):
        """Create an instance of a project history task object."""
        super(ProjectHistoryTask, self).__init__(json, api)
        self.task_name = name


class ProjectHistoryBuild(_BaseEvergreenObject):
    """
    Representation of a project history build in evergreen.
    """
    build_id = evg_attrib('build_id')
    display_name = evg_attrib('name')

    def __init__(self, name, json, api):
        """Create an instance of a project history build object."""
        super(ProjectHistoryBuild, self).__init__(json, api)
        self.build_name = name

    @property
    def tasks(self):
        return [ProjectHistoryTask(key, value, self._api) for key, value in
                self.json['tasks'].items()]


class ProjectHistoryVersion(_BaseEvergreenObject):
    """
    Representation of a project history version in evergreen.
    """
    version_id = evg_attrib('version_id')
    author = evg_attrib('author')
    revision = evg_attrib('revision')
    message = evg_attrib('message')

    def __init__(self, json, api):
        """Create an instance of a project history version object."""
        super(ProjectHistoryVersion, self).__init__(json, api)

    @property
    def builds(self):
        return [ProjectHistoryBuild(key, value, self._api) for key, value in
                self.json['builds'].items()]


class ProjectHistory(_BaseEvergreenObject):
    """
    Representation of a project's history evergreen.
    """
    project = evg_attrib('project')

    def __init__(self, json, api):
        """Create an instance of a project's history object."""
        super(ProjectHistory, self).__init__(json, api)

    @property
    def versions(self):
        """
        Get the versions data.

        :return: versions data.
        """
        return [ProjectHistoryVersion(version, self._api) for version in self.json['versions']]
