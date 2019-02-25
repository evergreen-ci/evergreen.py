# -*- encoding: utf-8 -*-
"""Evergreen representation of a project."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject


class Project(_BaseEvergreenObject):
    """Representation of an Evergreen project."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen project.

        :param json: json representing project.
        :param api: evergreen api object.
        """
        super(Project, self).__init__(json, api)
