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
