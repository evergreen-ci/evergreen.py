# -*- encoding: utf-8 -*-
"""Version representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib

_EVG_DATE_FIELDS_IN_VERSION = frozenset([
    'create_time',
    'finish_time',
    'start_time',
])


class BuildVariantStatus(_BaseEvergreenObject):
    """Representation of a Build Variants status."""

    build_variant = evg_attrib('build_variant')
    build_id = evg_attrib('build_id')

    def __init__(self, json, api):
        """Create an instance of a Build Variants status."""
        super(BuildVariantStatus, self).__init__(json, api)

    def get_build(self):
        """Get the build object for this build variants status."""
        return self._api.build_by_id(self.build_id)


class Version(_BaseEvergreenObject):
    """Representation of a Evergreen Version."""

    version_id = evg_attrib('version_id')
    create_time = evg_datetime_attrib('create_time')
    start_time = evg_datetime_attrib('start_time')
    finish_time = evg_datetime_attrib('finish_time')
    revision = evg_attrib('revision')
    order = evg_attrib('order')
    project = evg_attrib('project')
    author = evg_attrib('author')
    author_email = evg_attrib('author_email')
    message = evg_attrib('message')
    status = evg_attrib('status')
    repo = evg_attrib('repo')
    branch = evg_attrib('branch')
    errors = evg_attrib('errors')
    warnings = evg_attrib('warnings')
    ignored = evg_attrib('ignored')

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

    def get_builds(self):
        """
        Get all the builds that are a part of this version.

        :return: List of build that are a part of this version.
        """
        return self._api.builds_by_version(self.version_id)

    def is_patch(self):
        """
        Determine if this version from a patch build.

        :return: True if this version is a patch build.
        """
        return not self.version_id.startswith(self.project.replace('-', '_'))
