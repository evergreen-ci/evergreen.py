import json

from evergreen import Manifest, TaskStats, TestStats, Version

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import pytest
from click.testing import CliRunner

import evergreen.cli.main as under_test
from evergreen.host import Host
from evergreen.patch import Patch
from evergreen.project import Project

output_formats = [
    "--json",
    "--yaml",
    None,
]


@pytest.fixture(params=output_formats)
def output_fmt(request):
    return request.param


def _create_api_mock(monkeypatch):
    mock_generator = MagicMock()
    evg_api_mock = mock_generator.get_api.return_value
    monkeypatch.setattr(under_test, "EvergreenApi", mock_generator)
    return evg_api_mock


def test_list_hosts(monkeypatch, sample_host, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    evg_api_mock.all_hosts.return_value = [Host(sample_host, None)]

    runner = CliRunner()
    cmd_list = [output_fmt, "list-hosts"] if output_fmt else ["list-hosts"]
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_host["host_id"] in result.output


def test_list_patches(monkeypatch, sample_patch, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    evg_api_mock.patches_by_project.return_value = [Patch(sample_patch, None) for _ in range(10)]

    runner = CliRunner()
    cmd_list = ["list-patches", "--project", "project", "--limit", "5"]
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    if output_fmt == "--json":
        assert len(json.loads(result.output)) == 5
    assert sample_patch["patch_id"] in result.output


def test_list_projects(monkeypatch, sample_project, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    evg_api_mock.all_projects.return_value = [Project(sample_project, None) for _ in range(10)]

    runner = CliRunner()
    cmd_list = ["list-projects"]
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_project["identifier"] in result.output


def test_list_versions(monkeypatch, sample_version, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    evg_api_mock.versions_by_project.return_value = [
        Version(sample_version, None) for _ in range(10)
    ]

    runner = CliRunner()
    cmd_list = ["list-versions", "--project", "project", "--limit", "5"]
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    if output_fmt == "--json":
        assert len(json.loads(result.output)) == 5
    assert sample_version["version_id"] in result.output


def test_send_slack_message(monkeypatch):
    evg_api_mock = _create_api_mock(monkeypatch)
    mock_send_slack_message = MagicMock()
    evg_api_mock.send_slack_message = mock_send_slack_message

    runner = CliRunner()
    cmd_list = ["send-slack-message", "--target", "test_target", "--msg", "test_msg"]
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert mock_send_slack_message.call_count == 1
    assert mock_send_slack_message.call_args[0] == ("test_target", "test_msg")


def test_test_stats(monkeypatch, sample_test_stats, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    mock_test_stats = MagicMock()
    evg_api_mock.test_stats_by_project = mock_test_stats
    evg_api_mock.test_stats_by_project.return_value = [
        TestStats(sample_test_stats, None) for _ in range(10)
    ]

    cmd_list = ["test-stats", "-a", "after-date", "-b", "before-date", "-p", "project"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_test_stats["test_file"] in result.output
    assert "after-date" in mock_test_stats.call_args[0]
    assert "before-date" in mock_test_stats.call_args[0]
    assert "project" in mock_test_stats.call_args[0]


def test_task_stats(monkeypatch, sample_task_stats, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    mock_task_stats = MagicMock()
    evg_api_mock.task_stats_by_project = mock_task_stats
    evg_api_mock.task_stats_by_project.return_value = [
        TaskStats(sample_task_stats, None) for _ in range(10)
    ]

    cmd_list = ["task-stats", "-a", "after-date", "-b", "before-date", "-p", "project"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_task_stats["task_name"] in result.output
    assert "after-date" in mock_task_stats.call_args[0]
    assert "before-date" in mock_task_stats.call_args[0]
    assert "project" in mock_task_stats.call_args[0]


def test_task_reliability(monkeypatch, sample_task_reliability, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    mock_task_reliability = MagicMock()
    evg_api_mock.task_reliability_by_project = mock_task_reliability
    evg_api_mock.task_reliability_by_project.return_value = [
        TaskStats(sample_task_reliability, None) for _ in range(10)
    ]

    cmd_list = ["task-reliability", "-p", "project", "-t", "task1", "-t", "task2"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_task_reliability["task_name"] in result.output
    assert "project" in mock_task_reliability.call_args[0]
    assert ("task1", "task2") in mock_task_reliability.call_args[0]


def test_version_stats(monkeypatch, output_fmt):
    mock_version_metrics = MagicMock()
    mock_version_metrics.as_dict.return_value = "get_metrics_as_dict"

    mock_version = MagicMock(version_id="version_id")
    mock_version.get_metrics.return_value = mock_version_metrics if output_fmt else "get_metrics"

    evg_api_mock = _create_api_mock(monkeypatch)
    mock_version_by_id = MagicMock()
    evg_api_mock.version_by_id = mock_version_by_id
    evg_api_mock.version_by_id.return_value = mock_version

    cmd_list = ["version-stats", "-v", "version_id"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert "get_metrics_as_dict" in result.output if output_fmt else "get_metrics"
    assert "version_id" in mock_version_by_id.call_args[0]


def test_build_stats(monkeypatch, output_fmt):
    mock_build_metrics = MagicMock()
    mock_build_metrics.as_dict.return_value = "get_metrics_as_dict"

    mock_build = MagicMock(build_id="build_id")
    mock_build.get_metrics.return_value = mock_build_metrics if output_fmt else "get_metrics"

    evg_api_mock = _create_api_mock(monkeypatch)
    mock_build_by_id = MagicMock()
    evg_api_mock.build_by_id = mock_build_by_id
    evg_api_mock.build_by_id.return_value = mock_build

    cmd_list = ["build-stats", "-b", "build_id"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert "get_metrics_as_dict" in result.output if output_fmt else "get_metrics"
    assert "build_id" in mock_build_by_id.call_args[0]


def test_manifest(monkeypatch, sample_manifest, output_fmt):
    evg_api_mock = _create_api_mock(monkeypatch)
    mock_manifest = MagicMock()
    evg_api_mock.manifest = mock_manifest
    evg_api_mock.manifest.return_value = Manifest(sample_manifest, None)

    cmd_list = ["manifest", "--project", "project", "--commit", "commit"]

    runner = CliRunner()
    if output_fmt:
        cmd_list = [output_fmt] + cmd_list
    result = runner.invoke(under_test.cli, cmd_list)
    assert result.exit_code == 0
    assert sample_manifest["id"] in result.output
    assert "project" in mock_manifest.call_args[0]
    assert "commit" in mock_manifest.call_args[0]
