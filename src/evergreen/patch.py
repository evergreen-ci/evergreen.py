from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

_EVG_DATE_FIELDS_IN_PATCH = frozenset([
    'create_time',
    'start_time',
    'finish_time',
])


class Patch(_BaseEvergreenObject):
    """
    Representation of an Evergreen patch.
    """

    def __init__(self, json, api):
        """
        Create an instance of an evergreen patch.

        :param json: json representing patch.
        """
        super(Patch, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_PATCH
