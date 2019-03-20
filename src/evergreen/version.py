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

        if 'build_variants_status' in self.json:
            self.build_variants_map = {
                bvs['build_variant']: bvs['build_id']
                for bvs in self.json['build_variants_status']
            }

    @property
    def build_variants_status(self):
        build_variants_status = self.json['build_variants_status']
        return [BuildVariantStatus(bvs, self._api) for bvs in build_variants_status]

    def build_by_variant(self, build_variant):
        """
        Get a build object for the specified variant.

        :param build_variant: Build variant to get build for.
        :return: Build object for variant.
        """
        return self._api.build_by_id(self.build_variants_map[build_variant])

    def get_manifest(self):
        """
        Get the manifest for this version.

        :return: Manifest for this version.
        """
        return self._api.manifest(self.project, self.revision)
