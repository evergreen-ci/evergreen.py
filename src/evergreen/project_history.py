# -*- encoding: utf-8 -*-
"""Project history representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib


class Version(_BaseEvergreenObject):
    """
    Representation of a project version in evergreen.
    """
    version_id = evg_attrib('version_id')
    author = evg_attrib('author')
    revision = evg_attrib('revision')
    message = evg_attrib('message')
    builds = evg_attrib('builds')

    def __init__(self, json, api):
        """Create an instance of a project version object."""
        super(Version, self).__init__(json, api)


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
        return [Version(version, self._api) for version in self.json['versions']]
