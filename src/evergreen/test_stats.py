# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.util import parse_evergreen_datetime


_EVG_DATE_FIELDS_IN_TEST_STATS = frozenset([
    'date',
])


class TestStats(object):
    """Representation of an Evergreen test stats object."""

    def __init__(self, test_stats_json):
        """
        Create an instance of a test stats object.

        :param test_stats_json: json version of object.
        """
        self.json = test_stats_json

    def __getattr__(self, item):
        if item in self.json:
            if item in _EVG_DATE_FIELDS_IN_TEST_STATS and self.json[item]:
                return parse_evergreen_datetime(self.json[item])
            return self.json[item]
        raise TypeError('Unknown test stats attribute {0}'.format(item))
