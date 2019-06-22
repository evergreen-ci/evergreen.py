# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from evergreen.manifest import Manifest
from evergreen.metrics.versionmetrics import VersionMetrics
from evergreen.version import Version


SAMPLE_VERSION_ID_FOR_PATCH = '5c9e8453d6d80a457091d74e'


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

        sample_version['version_id'] = SAMPLE_VERSION_ID_FOR_PATCH
        version = Version(sample_version, None)
        assert version.is_patch()

    def test_get_builds(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)
        assert version.get_builds() == mock_api.builds_by_version.return_value

    def test_build_by_variant(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)
        build_variant = sample_version['build_variants_status'][0]

        build = version.build_by_variant(build_variant['build_variant'])
        assert build == mock_api.build_by_id.return_value
        mock_api.build_by_id.assert_called_once_with(build_variant['build_id'])

    def test_get_patch_for_non_patch(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        assert not version.get_patch()

    def test_get_patch_for_patch(self, sample_version):
        sample_version['version_id'] = SAMPLE_VERSION_ID_FOR_PATCH
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        assert version.get_patch() == mock_api.patch_by_id.return_value

    def test_started_version_is_not_completed(self, sample_version):
        sample_version['status'] = 'started'
        version = Version(sample_version, None)

        assert not version.is_completed()

    def test_failed_version_is_completed(self, sample_version):
        sample_version['status'] = 'failed'
        version = Version(sample_version, None)

        assert version.is_completed()

    def test_get_metrics_uncompleted(self, sample_version):
        sample_version['status'] = 'started'
        version = Version(sample_version, None)

        assert not version.get_metrics()

    def test_get_metrics_completed(self, sample_version):
        sample_version['status'] = 'failed'
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        metrics = version.get_metrics()
        assert isinstance(metrics, VersionMetrics)
