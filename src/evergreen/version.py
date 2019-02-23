# -*- encoding: utf-8 -*-
"""Version representation of evergreen."""
from __future__ import absolute_import

from evergreen.util import parse_evergreen_datetime


_EVG_DATE_FIELDS_IN_VERSION = frozenset([
    'create_time',
    'finish_time',
    'start_time',
])


class BuildVariantStatus(object):
    def __init__(self, build_variant_json, api):
        self.json = build_variant_json
        self._api = api

    def __getattr__(self, item):
        if item in self.json:
            return self.json[item]
        raise TypeError('Unknown version attribute {0}'.format(item))

    def get_build(self):
        return self._api.build_by_id(self.build_id)


class Version(object):
    def __init__(self, version_json, api):
        """
        Create an instance of an evergreen version.

        :param version_json: json representing version
        """
        self.json = version_json
        self._api = api

    def __getattr__(self, item):
        if item in self.json:
            if item in _EVG_DATE_FIELDS_IN_VERSION and self.json[item]:
                return parse_evergreen_datetime(self.json[item])
            return self.json[item]
        raise TypeError('Unknown version attribute {0}'.format(item))

    @property
    def build_variants_status(self):
        build_variants_status = self.json['build_variants_status']
        return [BuildVariantStatus(bvs, self._api) for bvs in build_variants_status]
