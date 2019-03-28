# -*- encoding: utf-8 -*-
"""Test representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

_EVG_DATE_FIELDS_IN_TEST = frozenset([
    'start_time',
    'end_time',
])


class Logs(_BaseEvergreenObject):
    """Representation of test logs from evergreen."""

    def __init__(self, json, api):
        super(Logs, self).__init__(json, api)


class Tst(_BaseEvergreenObject):
    """
    Representation of a test object from evergreen.
    """

    def __init__(self, json, api):
        super(Tst, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_TEST

    @property
    def logs(self):
        return Logs(self.json['logs'], self._api)
