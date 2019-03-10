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

    def get_version(self):
        """
        Get version for this patch.

        :return: Version object.
        """
        return self._api.version_by_id(self.version)

    def __str__(self):
        return '{}: {}'.format(self.patch_id, self.description)
