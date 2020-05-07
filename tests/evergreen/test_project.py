# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/project.py."""
from __future__ import absolute_import

from unittest.mock import MagicMock

from evergreen.project import Project


class TestProject(object):
    def test_most_recent_version(self, sample_project):
        mock_api = MagicMock()
        project = Project(sample_project, mock_api)
        mock_api.versions_by_project.return_value = (
            MagicMock(version_id=f"version_{i}") for i in range(3)
        )

        most_recent_version = project.most_recent_version()

        assert most_recent_version.version_id == "version_0"

    def test_module_by_name(self, sample_project):
        mock_api = MagicMock()
        project = Project(sample_project, mock_api)
        version_mock = MagicMock()
        my_module_mock = MagicMock()
        version_mock.get_manifest.return_value = MagicMock(modules={"my-module": my_module_mock})
        versions = [version_mock]
        mock_api.versions_by_project.return_value = (v for v in versions)

        module = project.module_by_name("my-module")

        assert module == my_module_mock

    def test_module_does_not_exist(self, sample_project):
        mock_api = MagicMock()
        project = Project(sample_project, mock_api)
        version_mock = MagicMock(version_id="lydia")
        version_mock.get_manifest.return_value = MagicMock(modules={"not-my-module": MagicMock()})
        versions = [version_mock]
        mock_api.versions_by_project.return_value = (v for v in versions)

        module = project.module_by_name("my-module")

        assert not module
