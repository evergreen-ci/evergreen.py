# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function


class Task(object):
    """Representation of an Evergreen task."""
    def __init__(self, task_json):
        """
        Create an instance of an evergreen task.
        """
        self.json = task_json

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown attribute {0}'.format(item))
