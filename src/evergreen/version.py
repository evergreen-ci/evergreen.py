# -*- encoding: utf-8 -*-
"""Version representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

_EVG_DATE_FIELDS_IN_VERSION = frozenset([
    'create_time',
    'finish_time',
    'start_time',
])


class BuildVariantStatus(_BaseEvergreenObject):
    def __init__(self, json, api):
        super(BuildVariantStatus, self).__init__(json, api)

    def get_build(self):
        return self._api.build_by_id(self.build_id)


class Version(_BaseEvergreenObject):
    def __init__(self, json, api):
        """
        Create an instance of an evergreen version.

        :param json: json representing version
        """
        super(Version, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_VERSION

    @property
    def build_variants_status(self):
        build_variants_status = self.json['build_variants_status']
        return [BuildVariantStatus(bvs, self._api) for bvs in build_variants_status]
