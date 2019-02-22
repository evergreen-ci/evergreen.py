from __future__ import absolute_import

from evergreen.util import parse_evergreen_datetime


_EVG_DATE_FIELDS_IN_PATCH = frozenset([
    'create_time',
    'start_time',
    'finish_time',
])


class Patch(object):
    """
    Representation of an Evergreen patch.
    """

    def __init__(self, patch_json):
        """
        Create an instance of an evergreen patch.

        :param patch_json: json representing patch.
        """
        self.json = patch_json

    def __getattr__(self, item):
        if item in self.json:
            if item in _EVG_DATE_FIELDS_IN_PATCH and self.json[item]:
                return parse_evergreen_datetime(self.json[item])
            return self.json[item]
        raise TypeError('Unknown patch attribute {0}'.format(item))
