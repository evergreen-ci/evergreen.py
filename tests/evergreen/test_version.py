# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from evergreen.manifest import Manifest
from evergreen.version import Version


class TestVersion(object):
    def test_get_attributes(self, sample_version):
        version = Version(sample_version, None)
        assert version.version_id == sample_version['version_id']

    def test_dates_are_correct(self, sample_version):
        version = Version(sample_version, None)
        assert isinstance(version.create_time, datetime)

    def test_build_variant_status(self, sample_version):
        version = Version(sample_version, None)
        assert len(sample_version['build_variants_status']) == len(version.build_variants_status)

    def test_get_manifest(self, sample_version, sample_manifest):
        mock_api = MagicMock()
        mock_api.manifest.return_value = Manifest(sample_manifest, None)
        version = Version(sample_version, mock_api)
        manifest = version.get_manifest()

        mock_api.manifest.assert_called_with(sample_version['project'], sample_version['revision'])
        assert len(manifest.modules) == len(sample_manifest['modules'])

    def test_is_patch(self, sample_version):
        version = Version(sample_version, None)
        assert not version.is_patch()

        sample_version['version_id'] = '5c9e8453d6d80a457091d74e'
        version = Version(sample_version, None)
        assert version.is_patch()

    def test_get_builds(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)
        assert version.get_builds() == mock_api.builds_by_version.return_value
