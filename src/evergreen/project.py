# -*- encoding: utf-8 -*-
"""Evergreen representation of a project."""
from __future__ import absolute_import


class Project(object):
    """Representation of an Evergreen project."""
    def __init__(self, project_json, api):
        """
        Create an instance of an evergreen project.

        :param project_json: json representing project.
        :param api: evergreen api object.
        """
        self.json = project_json
        self._api = api

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown project attribute {0}'.format(item))

    def get_patches(self):
        return self._api.get_patches_per_project(self.identifier, params={'limit': 5})
