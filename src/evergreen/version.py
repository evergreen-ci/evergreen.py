# -*- encoding: utf-8 -*-
"""Version representation of evergreen."""
from __future__ import absolute_import


class Version(object):
    def __init__(self, version_json):
        """
        Create an instance of an evergreen version.

        :param version_json: json representing version
        """
        self.json = version_json

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown version attribute {0}'.format(item))
