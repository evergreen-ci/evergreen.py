# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function


class Build(object):
    """Representation of an Evergreen build."""
    def __init__(self, build_json):
        """
        Create an instance of an evergreen task.
        """
        self.json = build_json

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown build attribute {0}'.format(item))
