# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from evergreen.manifest import Manifest
from evergreen.metrics.versionmetrics import VersionMetrics
from evergreen.version import RecentVersions, Requester, Version

SAMPLE_VERSION_ID_FOR_PATCH = "5c9e8453d6d80a457091d74e"
EXPECTED_REQUESTER_PAIRS = [
    (Requester.PATCH_REQUEST, "patch"),
    (Requester.GITTER_REQUEST, "mainline"),
    (Requester.GITHUB_PULL_REQUEST, "patch"),
    (Requester.AD_HOC, "adhoc"),
    (Requester.TRIGGER_REQUEST, "trigger"),
]


class TestRequester(object):
    @pytest.mark.parametrize(["requester", "value"], EXPECTED_REQUESTER_PAIRS)
    def test_stats_value(self, requester, value):
        assert requester.stats_value() == value


class TestVersion(object):
    def test_get_attributes(self, sample_version):
        version = Version(sample_version, None)
        assert version.version_id == sample_version["version_id"]

    def test_dates_are_correct(self, sample_version):
        version = Version(sample_version, None)
        assert isinstance(version.create_time, datetime)

    def test_build_variant_status(self, sample_version):
        version = Version(sample_version, None)
        assert len(sample_version["build_variants_status"]) == len(version.build_variants_status)

    def test_missing_build_variant_status(self, sample_version):
        del sample_version["build_variants_status"]
        version = Version(sample_version, None)

        assert not version.build_variants_status

        sample_version["build_variants_status"] = None
        version = Version(sample_version, None)

        assert not version.build_variants_status

    def test_get_manifest(self, sample_version, sample_manifest):
        mock_api = MagicMock()
        mock_api.manifest.return_value = Manifest(sample_manifest, None)
        version = Version(sample_version, mock_api)
        manifest = version.get_manifest()

        mock_api.manifest.assert_called_with(sample_version["project"], sample_version["revision"])
        assert len(manifest.modules) == len(sample_manifest["modules"])

    def test_get_modules(self, sample_version, sample_manifest):
        mock_api = MagicMock()
        mock_api.manifest.return_value = Manifest(sample_manifest, None)
        version = Version(sample_version, mock_api)
        modules = version.get_modules()

        assert len(modules) == len(sample_manifest["modules"])

    def test_is_patch_with_requester(self, sample_version):
        del sample_version["requester"]
        version = Version(sample_version, None)
        assert not version.is_patch()

        sample_version["version_id"] = SAMPLE_VERSION_ID_FOR_PATCH
        version = Version(sample_version, None)
        assert version.is_patch()

    def test_is_patch(self, sample_version):
        sample_version["requester"] = Requester.GITTER_REQUEST.evg_value()
        version = Version(sample_version, None)
        assert not version.is_patch()

        sample_version["requester"] = Requester.PATCH_REQUEST.evg_value()
        version = Version(sample_version, None)
        assert version.is_patch()

    def test_requester(self, requester_value, sample_version):
        sample_version["requester"] = requester_value.evg_value()
        version = Version(sample_version, None)
        assert version.requester == requester_value

    def test_get_builds(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)
        assert version.get_builds() == mock_api.builds_by_version.return_value

    def test_build_by_variant(self, sample_version):
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)
        build_variant = sample_version["build_variants_status"][0]

        build = version.build_by_variant(build_variant["build_variant"])
        assert build == mock_api.build_by_id.return_value
        mock_api.build_by_id.assert_called_once_with(build_variant["build_id"])

    def test_get_patch_for_non_patch(self, sample_version):
        sample_version["requester"] = Requester.GITTER_REQUEST.evg_value()
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        assert not version.get_patch()

    def test_get_patch_for_patch(self, sample_version):
        sample_version["version_id"] = SAMPLE_VERSION_ID_FOR_PATCH
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        assert version.get_patch() == mock_api.patch_by_id.return_value

    def test_started_version_is_not_completed(self, sample_version):
        sample_version["status"] = "started"
        version = Version(sample_version, None)

        assert not version.is_completed()

    def test_failed_version_is_completed(self, sample_version):
        sample_version["status"] = "failed"
        version = Version(sample_version, None)

        assert version.is_completed()

    def test_get_metrics_uncompleted(self, sample_version):
        sample_version["status"] = "created"
        version = Version(sample_version, None)

        assert not version.get_metrics()

    def test_get_metrics_completed(self, sample_version):
        sample_version["status"] = "failed"
        mock_api = MagicMock()
        version = Version(sample_version, mock_api)

        metrics = version.get_metrics()
        assert isinstance(metrics, VersionMetrics)


class TestRecentVersions:
    def test_row_map_should_be_querable(self, sample_recent_versions):
        recent_versions = RecentVersions(sample_recent_versions, None)

        assert len(recent_versions.row_map) == len(sample_recent_versions["rows"])
        example_build_name = list(sample_recent_versions["rows"].keys())[2]
        example_build_variant = sample_recent_versions["rows"][example_build_name]["build_variant"]
        assert recent_versions.row_map[example_build_name].build_variant == example_build_variant

    def test_builds_in_row_should_be_querable(self, sample_recent_versions):
        recent_versions = RecentVersions(sample_recent_versions, None)

        example_build_name = list(sample_recent_versions["rows"].keys())[4]
        example_builds = sample_recent_versions["rows"][example_build_name]["builds"]
        example_build = list(example_builds.keys())[1]

        build = recent_versions.row_map[example_build_name].builds[example_build]
        assert build.version == example_builds[example_build]["version"]
