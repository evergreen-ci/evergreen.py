# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/host.py."""
from __future__ import absolute_import

from evergreen.distro import Distro


class TestDistro:
    def test_get_attributes(self, sample_distro):
        distro = Distro(sample_distro, None)

        assert distro.name == sample_distro['name']
        assert distro.provider == sample_distro['provider']
        assert distro.planner_settings.version == sample_distro['planner_settings']['version']
        assert distro.finder_settings.version == sample_distro['finder_settings']['version']

    def test_settings(self, sample_distro):
        distro = Distro(sample_distro, None)
        settings = distro.settings
        setting_json = sample_distro['settings']

        assert settings.ami == setting_json['ami']

        mount_point = settings.mount_points[0]
        assert mount_point.device_name == setting_json['mount_points'][0]['device_name']

    def test_expansions(self, sample_distro):
        distro = Distro(sample_distro, None)

        for expansion in sample_distro['expansions']:
            assert distro.expansions[expansion['key']] == expansion['value']

    def test_missing_attributes(self, sample_distro):
        del sample_distro['settings']
        distro = Distro(sample_distro, None)

        assert not distro.settings

    def test_missing_mount_points(self, sample_distro):
        del sample_distro['settings']['mount_points']
        distro = Distro(sample_distro, None)

        assert not distro.settings.mount_points
