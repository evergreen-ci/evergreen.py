# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.util import parse_evergreen_datetime


class _BaseEvergreenObject(object):
    """Common evergreen object."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        self.json = json
        self._api = api
        self._date_fields = None

    def _is_field_a_date(self, item):
        return self._date_fields and item in self._date_fields and self.json[item]

    def __getattr__(self, item):
        """Lookup an attribute if it exists."""
        if item in self.json:
            if self._is_field_a_date(item):
                return parse_evergreen_datetime(self.json[item])
            return self.json[item]
        raise TypeError('Unknown attribute {0}'.format(item))
