# -*- encoding: utf-8 -*-
"""Stats representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

_EVG_DATE_FIELDS_IN_TEST_STATS = frozenset([
    'date',
])


class TestStats(_BaseEvergreenObject):
    """Representation of an Evergreen test stats object."""

    def __init__(self, json, api):
        """
        Create an instance of a test stats object.

        :param json: json version of object.
        """
        super(TestStats, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_TEST_STATS
