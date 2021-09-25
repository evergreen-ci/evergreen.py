import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.exceptions import HTTPError

import evergreen.api as under_test
from evergreen.api_requests import IssueLinkRequest, SlackAttachment
from evergreen.config import DEFAULT_API_SERVER, DEFAULT_NETWORK_TIMEOUT_SEC
from evergreen.resource_type_permissions import PermissionableResourceType, RemovablePermission
from evergreen.util import EVG_DATETIME_FORMAT, parse_evergreen_datetime
from evergreen.version import Requester


def ns(relative):
    return "evergreen.api." + relative


def from_iso_format(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


class TestConfiguration(object):
    def test_uses_passed_auth(self, sample_evergreen_auth):
        kwargs = under_test.EvergreenApi._setup_kwargs(auth=sample_evergreen_auth)
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC

    @patch(ns("read_evergreen_config"))
    def test_uses_default_config_file(
        self, mock_read_evergreen_config, sample_evergreen_configuration, sample_evergreen_auth
    ):
        mock_read_evergreen_config.return_value = sample_evergreen_configuration
        kwargs = under_test.EvergreenApi._setup_kwargs(use_config_file=True)
        mock_read_evergreen_config.assert_called_once()
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC

    @patch(ns("read_evergreen_from_file"))
    def test_uses_passed_config_file(
        self, read_evergreen_from_file, sample_evergreen_configuration, sample_evergreen_auth
    ):
        read_evergreen_from_file.return_value = sample_evergreen_configuration
        kwargs = under_test.EvergreenApi._setup_kwargs(config_file="config.yml")
        read_evergreen_from_file.assert_called_once_with("config.yml")
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC


class TestRaiseForStatus(object):
    @pytest.mark.skipif(
        sys.version_info.major == 2, reason="JSONDecodeError is not used in python2"
    )
    def test_non_json_error(self, mocked_api):
        mocked_response = MagicMock()
        mocked_response.json.side_effect = JSONDecodeError("json error", "", 0)
        mocked_response.status_code = 500
        mocked_response.raise_for_status.side_effect = HTTPError()
        mocked_api.session.request.return_value = mocked_response

        with pytest.raises(HTTPError):
            mocked_api.version_by_id("version_id")

        mocked_response.raise_for_status.assert_called_once()

    def test_json_errors_are_passed_through(self, mocked_api):
        error_msg = "the error"
        mocked_response = MagicMock()
        mocked_response.json.return_value = {"error": error_msg}
        mocked_response.status_code = 500
        mocked_response.raise_for_status.side_effect = HTTPError()
        mocked_api.session.request.return_value = mocked_response

        with pytest.raises(HTTPError) as excinfo:
            mocked_api.version_by_id("version_id")

        assert error_msg in str(excinfo.value)
        mocked_response.raise_for_status.assert_not_called()


class TestLazyPagination(object):
    def test_with_no_next(self, mocked_api):
        returned_items = ["item 1", "item 2", "item 3"]
        mocked_api.session.request.return_value.json.return_value = returned_items

        results = mocked_api._lazy_paginate("http://url")

        result_count = 0
        for result in results:
            assert result in returned_items
            result_count += 1

        assert len(returned_items) == result_count

    def test_next_in_response(self, mocked_api):
        returned_items = ["item 1", "item 2", "item 3"]
        next_url = "http://url_to_next"
        mocked_api.session.request.return_value.json.return_value = returned_items
        mocked_api.session.request.return_value.links = {"next": {"url": next_url}}

        results = mocked_api._lazy_paginate("http://url")

        items_to_check = len(returned_items) * 3
        for i, result in enumerate(results):
            assert result in returned_items
            if i > items_to_check:
                break

        assert i > items_to_check


class TestSessions(object):
    def test_session_can_be_created(self):
        evg_api = under_test.EvergreenApi()

        session_instance_one = evg_api.session
        session_instance_two = evg_api.session

        assert session_instance_one is not None
        assert session_instance_two is not None
        assert session_instance_one != session_instance_two

    def test_with_session_creates_a_new_session(self):
        original_evg_api = under_test.EvergreenApi()

        with original_evg_api.with_session() as evg_api_with_session:
            session_instance_one = evg_api_with_session.session
            session_instance_two = evg_api_with_session.session

            assert session_instance_one == session_instance_two
            assert original_evg_api.session != evg_api_with_session.session


class TestDistrosApi(object):
    def test_all_distros(self, mocked_api):
        mocked_api.all_distros()
        mocked_api.session.request.assert_called_with(
            url=mocked_api._create_url("/distros"),
            params=None,
            timeout=None,
            data=None,
            method="GET",
        )


class TestHostApi(object):
    def test_all_hosts(self, mocked_api):
        mocked_api.all_hosts()
        mocked_api.session.request.assert_called_with(
            url=mocked_api._create_url("/hosts"), params={}, timeout=None, data=None, method="GET"
        )

    def test_all_hosts_with_status(self, mocked_api):
        mocked_api.all_hosts(status="success")
        mocked_api.session.request.assert_called_with(
            url=mocked_api._create_url("/hosts"),
            params={"status": "success"},
            timeout=None,
            data=None,
            method="GET",
        )


class TestProjectApi(object):
    def test_all_projects(self, mocked_api):
        mocked_api.all_projects()
        expected_url = mocked_api._create_url("/projects")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_all_projects_with_filter(self, mocked_api, mocked_api_response, sample_projects):
        mocked_api_response.json.return_value = sample_projects

        def filter_fn(project):
            return project.identifier == "project 2"

        projects = mocked_api.all_projects(filter_fn)

        assert len(projects) == 1
        assert projects[0].identifier == "project 2"

    def test_project_by_id(self, mocked_api):
        mocked_api.project_by_id("project_id")
        expected_url = mocked_api._create_url("/projects/project_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_recent_version_by_project(self, mocked_api):
        mocked_api.recent_versions_by_project("project_id")
        expected_url = mocked_api._create_url("/projects/project_id/recent_versions")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_version_by_project(self, mocked_api):
        returned_versions = mocked_api.versions_by_project("project_id")
        expected_url = mocked_api._create_url("/projects/project_id/versions")
        expected_params = {"requester": "gitter_request"}
        next(returned_versions)
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_version_by_project_with_limit_and_start(self, mocked_api):
        start = 15
        limit = 20
        returned_versions = mocked_api.versions_by_project("project_id", start=start, limit=limit)
        expected_url = mocked_api._create_url("/projects/project_id/versions")
        expected_params = {"requester": "gitter_request", "start": start, "limit": limit}
        next(returned_versions)
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_alias_for_version(self, mocked_api):
        mocked_api.alias_for_version("version_id", "my_alias")
        expected_url = mocked_api._create_url("/projects/test_alias")
        expected_params = {"version": "version_id", "alias": "my_alias", "include_deps": False}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_versions_by_project_time_window(self, mocked_api, sample_version, mocked_api_response):
        version_list = [
            deepcopy(sample_version),
            deepcopy(sample_version),
            deepcopy(sample_version),
        ]
        # Create a window of 1 day, and set the dates so that only the middle items should be
        # returned.
        one_day = timedelta(days=1)
        one_hour = timedelta(hours=1)
        before_date = parse_evergreen_datetime(version_list[1]["create_time"])
        after_date = before_date - one_day

        version_list[0]["create_time"] = (before_date + one_day).strftime(EVG_DATETIME_FORMAT)
        version_list[1]["create_time"] = (before_date - one_hour).strftime(EVG_DATETIME_FORMAT)
        version_list[2]["create_time"] = (after_date - one_day).strftime(EVG_DATETIME_FORMAT)

        mocked_api_response.json.return_value = version_list

        windowed_versions = mocked_api.versions_by_project_time_window(
            "project_id", before_date, after_date
        )

        windowed_list = list(windowed_versions)

        assert len(windowed_list) == 1
        assert version_list[1]["version_id"] == windowed_list[0].version_id

    def test_patches_by_project(self, mocked_api):
        patches = mocked_api.patches_by_project("project_id")
        next(patches)
        expected_url = mocked_api._create_url("/projects/project_id/patches")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params={"limit": 100}, timeout=None, data=None, method="GET"
        )

    def test_patches_by_user(self, mocked_api):
        patches = mocked_api.patches_by_user("user_id")
        next(patches)
        expected_url = mocked_api._create_url("/users/user_id/patches")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params={"limit": 100}, timeout=None, data=None, method="GET"
        )

    def test_configure_patch(self, mocked_api):
        variants = ["my_variant", ["*"]]
        description = "mypatch"
        mocked_api.configure_patch("patch_id", description=description, variants=variants)
        expected_url = mocked_api._create_url("/patches/patch_id/configure")
        expected_data = json.dumps({"variants": variants, "description": description})
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="POST"
        )

    def test_configure_patch_variants(self, mocked_api):
        variants = ["my_variant", ["task_one", "task_two"]]
        mocked_api.configure_patch("patch_id", variants=variants)
        expected_url = mocked_api._create_url("/patches/patch_id/configure")
        expected_data = json.dumps({"variants": variants})
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="POST"
        )

    def test_patches_by_project_time_window(self, mocked_api, sample_patch, mocked_api_response):
        patch_list = [
            deepcopy(sample_patch),
            deepcopy(sample_patch),
            deepcopy(sample_patch),
        ]
        # Create a window of 1 day, and set the dates so that only the middle items should be
        # returned.
        one_day = timedelta(days=1)
        one_hour = timedelta(hours=1)
        before_date = parse_evergreen_datetime(patch_list[1]["create_time"])
        after_date = before_date - one_day

        patch_list[0]["create_time"] = (before_date + one_day).strftime(EVG_DATETIME_FORMAT)
        patch_list[1]["create_time"] = (before_date - one_hour).strftime(EVG_DATETIME_FORMAT)
        patch_list[2]["create_time"] = (after_date - one_day).strftime(EVG_DATETIME_FORMAT)

        mocked_api_response.json.return_value = patch_list

        windowed_versions = mocked_api.patches_by_project_time_window(
            "project_id", before_date, after_date
        )

        windowed_list = list(windowed_versions)

        assert len(windowed_list) == 1
        assert patch_list[1]["patch_id"] == windowed_list[0].patch_id

    def test_commit_queue_for_project(self, mocked_api):
        mocked_api.commit_queue_for_project("project_id")
        expected_url = mocked_api._create_url("/commit_queue/project_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_test_stats_by_project(self, mocked_api):
        after_date = "2019-01-01"
        before_date = "2019-02-01"
        expected_url = mocked_api._create_url("/projects/project_id/test_stats")
        expected_params = {
            "after_date": after_date,
            "before_date": before_date,
        }

        mocked_api.test_stats_by_project(
            "project_id", from_iso_format(after_date), from_iso_format(before_date),
        )

        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_test_stats_by_project_with_requester(self, mocked_api):
        after_date = "2019-01-01"
        before_date = "2019-02-01"
        expected_url = mocked_api._create_url("/projects/project_id/test_stats")
        expected_params = {
            "after_date": after_date,
            "before_date": before_date,
            "requesters": "patch",
        }

        mocked_api.test_stats_by_project(
            "project_id",
            from_iso_format(after_date),
            from_iso_format(before_date),
            requesters=Requester.PATCH_REQUEST,
        )

        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_single_test_by_task(self, mocked_api):
        mocked_api.single_test_by_task_and_test_file("task_id", "com.xgen.module.MyTests.test1")
        expected_url = mocked_api._create_url("/tasks/task_id/tests")
        mocked_api.session.request.assert_called_with(
            url=expected_url,
            params={"test_name": "com.xgen.module.MyTests.test1"},
            timeout=None,
            data=None,
            method="GET",
        )

    def test_send_slack_message(self, mocked_api):
        target = "@fake-user"
        msg = "I'm a fake message"
        mocked_api.send_slack_message(target, msg)
        expected_url = mocked_api._create_url("/notifications/slack")
        expected_data = json.dumps({"target": target, "msg": msg})
        mocked_api.session.request.assert_called_with(
            url=expected_url, timeout=None, data=expected_data, method="POST", params=None
        )

    def test_send_slack_message_with_attachments(self, mocked_api):
        target = "@fake-user"
        msg = "I'm a fake message"
        attachments = [
            SlackAttachment(text="Test Text", title="Test Title"),
            SlackAttachment(text="Fake text", title="Fake title"),
        ]
        mocked_api.send_slack_message(target, msg, attachments)
        expected_url = mocked_api._create_url("/notifications/slack")
        expected_data = json.dumps(
            {
                "target": target,
                "msg": msg,
                "attachments": [
                    att.dict(exclude_none=True, exclude_unset=True) for att in attachments
                ],
            }
        )
        mocked_api.session.request.assert_called_with(
            url=expected_url, timeout=None, data=expected_data, method="POST", params=None
        )

    def test_tasks_by_project(self, mocked_api):
        mocked_api.tasks_by_project("project_id")
        expected_url = mocked_api._create_url("/projects/project_id/versions/tasks")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_tasks_by_project_with_statuses(self, mocked_api):
        mocked_api.tasks_by_project("project_id", statuses=["status1"])
        expected_url = mocked_api._create_url("/projects/project_id/versions/tasks")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params={"status": ["status1"]}, timeout=None, data=None, method="GET"
        )


class TestTaskStatsByProject(object):
    def test_with_multiple_tasks(self, mocked_api):
        after_date = "2020-04-04"
        before_date = "2020-05-04"
        task_list = [f"task_{i}" for i in range(3)]
        expected_url = mocked_api._create_url("/projects/project_id/task_stats")
        expected_params = {
            "after_date": after_date,
            "before_date": before_date,
            "tasks": task_list,
        }

        mocked_api.task_stats_by_project(
            "project_id",
            after_date=from_iso_format(after_date),
            before_date=from_iso_format(before_date),
            tasks=task_list,
        )

        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )


class TestBuildApi(object):
    def test_build_by_id(self, mocked_api):
        mocked_api.build_by_id("build_id")
        expected_url = mocked_api._create_url("/builds/build_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_tasks_by_build(self, mocked_api):
        mocked_api.tasks_by_build("build_id")
        expected_url = mocked_api._create_url("/builds/build_id/tasks")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params={}, timeout=None, data=None, method="GET"
        )


class TestVersionApi(object):
    def test_version_by_id(self, mocked_api):
        mocked_api.version_by_id("version_id")
        expected_url = mocked_api._create_url("/versions/version_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_builds_by_version(self, mocked_api):
        mocked_api.builds_by_version("version_id")
        expected_url = mocked_api._create_url("/versions/version_id/builds")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )


class TestPatchApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.patch_by_id("patch_id")
        expected_url = mocked_api._create_url("/patches/patch_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )


class TestTaskApi(object):
    def test_task_by_id(self, mocked_api):
        mocked_api.task_by_id("task_id")
        expected_url = mocked_api._create_url("/tasks/task_id")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_task_by_id_with_fetch_executions(self, mocked_api):
        mocked_api.task_by_id("task_id", fetch_all_executions=True)
        expected_url = mocked_api._create_url("/tasks/task_id")
        expected_params = {"fetch_all_executions": True}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_manifest_for_task(self, mocked_api):
        mocked_api.manifest_for_task("task_id")
        expected_url = mocked_api._create_url("/tasks/task_id/manifest")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )

    def test_tests_by_task(self, mocked_api):
        mocked_api.tests_by_task("task_id")
        expected_url = mocked_api._create_url("/tasks/task_id/tests")
        expected_params = {}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_tests_by_task_with_status(self, mocked_api):
        mocked_api.tests_by_task("task_id", status="success")
        expected_url = mocked_api._create_url("/tasks/task_id/tests")
        expected_params = {"status": "success"}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_tests_by_task_with_execution(self, mocked_api):
        mocked_api.tests_by_task("task_id", execution=5)
        expected_url = mocked_api._create_url("/tasks/task_id/tests")
        expected_params = {"execution": 5}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_tests_by_task_with_status_and_execution(self, mocked_api):
        mocked_api.tests_by_task("task_id", status="success", execution=5)
        expected_url = mocked_api._create_url("/tasks/task_id/tests")
        expected_params = {"status": "success", "execution": 5}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_get_task_annotation(self, mocked_api):
        mocked_api.get_task_annotation("task_id", execution=5)
        expected_url = mocked_api._create_url("/tasks/task_id/annotations")
        expected_params = {"execution": 5}
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_get_task_annotation_with_invalid_parameters(self, mocked_api):
        with pytest.raises(ValueError):
            mocked_api.get_task_annotation("task_id", execution=5, fetch_all_executions=True)

    def test_annotate_task(self, mocked_api):
        mocked_api.annotate_task(
            "task_id",
            message="hello world",
            issues=[IssueLinkRequest(issue_key="key-1234", url="http://hello.world/key-1234")],
        )
        expected_url = mocked_api._create_url("/tasks/task_id/annotation")
        expected_params = None
        expected_data = json.dumps(
            {
                "task_id": "task_id",
                "note": {"message": "hello world"},
                "issues": [{"issue_key": "key-1234", "url": "http://hello.world/key-1234"}],
            }
        )
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=expected_data, method="PUT"
        )

    def test_annotate_task_with_zero_execution(self, mocked_api):
        mocked_api.annotate_task(
            "task_id",
            execution=0,
            message="hello world",
            issues=[IssueLinkRequest(issue_key="key-1234", url="http://hello.world/key-1234")],
        )
        expected_url = mocked_api._create_url("/tasks/task_id/annotation")
        expected_params = None
        expected_data = json.dumps(
            {
                "task_id": "task_id",
                "task_execution": 0,
                "note": {"message": "hello world"},
                "issues": [{"issue_key": "key-1234", "url": "http://hello.world/key-1234"}],
            }
        )
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=expected_data, method="PUT"
        )

    def test_performance_results_by_task(self, mocked_api):
        mocked_api.performance_results_by_task("task_id")
        expected_url = mocked_api._create_plugin_url("/task/task_id/perf")
        expected_params = None
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_performance_results_by_task_name(self, mocked_api):
        mocked_api.performance_results_by_task_name("task_id", "task_name")
        expected_url = "{api_server}/api/2/task/task_id/json/history/task_name/perf".format(
            api_server=DEFAULT_API_SERVER
        )
        expected_params = None
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_json_by_task(self, mocked_api):
        mocked_api.json_by_task("task_id", "json_key_id")
        expected_url = mocked_api._create_plugin_url("/task/task_id/json_key_id")
        expected_params = None
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_json_history_for_task(self, mocked_api):
        mocked_api.json_history_for_task("task_id", "task_name", "json_key_id")
        expected_url = f"{DEFAULT_API_SERVER}/api/2/task/task_id/json/history/task_name/json_key_id"
        expected_params = None
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="GET"
        )

    def test_restart_task(self, mocked_api):
        mocked_api.restart_task("task_id")
        expected_url = mocked_api._create_url("/tasks/task_id/restart")
        expected_params = None
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=expected_params, timeout=None, data=None, method="POST"
        )

    def test_abort_task(self, mocked_api):
        mocked_api.abort_task("task_id")
        expected_url = mocked_api._create_url("/tasks/task_id/abort")
        expected_params = None
        expected_data = None
        mocked_api.session.request.assert_called_with(
            url=expected_url,
            params=expected_params,
            timeout=None,
            data=expected_data,
            method="POST",
        )

    def test_configure_task_activate(self, mocked_api):
        mocked_api.configure_task("task_id", activated=True)
        expected_url = mocked_api._create_url("/tasks/task_id")
        expected_params = None
        expected_data = json.dumps({"activated": True})
        mocked_api.session.request.assert_called_with(
            url=expected_url,
            params=expected_params,
            timeout=None,
            data=expected_data,
            method="PATCH",
        )

    def test_configure_task_priority(self, mocked_api):
        mocked_api.configure_task("task_id", priority=100)
        expected_url = mocked_api._create_url("/tasks/task_id")
        expected_params = None
        expected_data = json.dumps({"priority": 100})
        mocked_api.session.request.assert_called_with(
            url=expected_url,
            params=expected_params,
            timeout=None,
            data=expected_data,
            method="PATCH",
        )

    def test_configure_task(self, mocked_api):
        mocked_api.configure_task("task_id", priority=100, activated=True)
        expected_url = mocked_api._create_url("/tasks/task_id")
        expected_params = None
        expected_data = json.dumps({"activated": True, "priority": 100})
        mocked_api.session.request.assert_called_with(
            url=expected_url,
            params=expected_params,
            timeout=None,
            data=expected_data,
            method="PATCH",
        )


class TestOldApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.manifest("project_id", "revision")
        expected_url = mocked_api._create_old_url("plugin/manifest/get/project_id/revision")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )


class TestLogApi(object):
    def test_retrieve_log(self, mocked_api):
        mocked_api.retrieve_task_log("log_url")
        mocked_api.session.request.assert_called_with(
            url="log_url", params={}, timeout=None, data=None, method="GET"
        )

    def test_retrieve_log_with_raw(self, mocked_api):
        mocked_api.retrieve_task_log("log_url", raw=True)
        mocked_api.session.request.assert_called_with(
            url="log_url", params={"text": "true"}, timeout=None, data=None, method="GET"
        )

    def test_stream_log(self, mocked_api):
        streamed_data = ["line_{}".format(i) for i in range(10)]
        mocked_response = MagicMock()
        mocked_response.iter_lines.return_value = streamed_data
        mocked_response.status_code = 200
        mocked_api.session.get.return_value.__enter__.return_value = mocked_response

        for line in mocked_api.stream_log("log_url"):
            assert line in streamed_data


class TestUserPermissionsApi(object):
    def test_permissions_for_user(self, mocked_api, mocked_api_response):
        expected_url = mocked_api._create_url("/users/test.user/permissions")
        permissions = [{"type": "project", "permissions": {"proj1": {"test": 1}}}]
        mocked_api_response.json.return_value = permissions
        returned_permissions = mocked_api.permissions_for_user("test.user")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )
        assert len(returned_permissions) == 1
        assert returned_permissions[0].resource_type == "project"
        assert returned_permissions[0].permissions == permissions[0]["permissions"]

    def test_give_permissions_to_user(self, mocked_api, mocked_api_response):
        expected_url = mocked_api._create_url("/users/test.user/permissions")
        resources = ["resource-1", "resource-2"]
        permissions = {"proj1": {"test": 1}}
        expected_data = json.dumps(
            {
                "resource_type": PermissionableResourceType.PROJECT.value,
                "resources": resources,
                "permissions": permissions,
            }
        )
        mocked_api.give_permissions_to_user(
            "test.user", PermissionableResourceType.PROJECT, resources, permissions
        )
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="POST",
        )

    def test_delete_user_permissions_all_resources(self, mocked_api):
        expected_url = mocked_api._create_url("/users/test.user/permissions")
        expected_data = json.dumps({"resource_type": RemovablePermission.PROJECT.value})
        mocked_api.delete_user_permissions("test.user", RemovablePermission.PROJECT)
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="DELETE",
        )

    def test_delete_user_permissions_specific_resource(self, mocked_api):
        expected_url = mocked_api._create_url("/users/test.user/permissions")
        expected_data = json.dumps(
            {"resource_type": RemovablePermission.PROJECT.value, "resource_id": "testresource"}
        )
        mocked_api.delete_user_permissions("test.user", RemovablePermission.PROJECT, "testresource")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="DELETE",
        )


class TestRolesApi(object):
    @pytest.mark.parametrize("create_user", [False, True])
    def test_give_roles_to_user(self, mocked_api, create_user):
        expected_url = mocked_api._create_url("/users/test.user/roles")
        roles = ["role1", "role2"]
        expected_data = json.dumps(
            {"user_id": "test.user", "roles": roles, "create_user": create_user}
        )
        mocked_api.give_roles_to_user("test.user", roles, create_user)
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=expected_data, method="POST"
        )

    def test_get_users_for_role(self, mocked_api, mocked_api_response):
        expected_url = mocked_api._create_url("/roles/testrole/users")
        users = ["test1", "test2", "test3"]
        mocked_api_response.json.return_value = {"users": users}
        returned_response = mocked_api.get_users_for_role("testrole")
        mocked_api.session.request.assert_called_with(
            url=expected_url, params=None, timeout=None, data=None, method="GET"
        )
        assert returned_response == {"users": users}


class TestCachedEvergreenApi(object):
    def test_build_by_id_is_cached(self, mocked_cached_api):
        build_id = "some build id"
        another_build_id = "some other build id"
        mocked_cached_api.build_by_id(build_id)
        mocked_cached_api.build_by_id(build_id)
        mocked_cached_api.build_by_id(another_build_id)
        assert mocked_cached_api.session.request.call_count == 2

    def test_version_by_id_is_cached(self, mocked_cached_api):
        version_id = "some version id"
        another_version_id = "some other version id"
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.version_by_id(another_version_id)
        assert mocked_cached_api.session.request.call_count == 2

    def test_clear_caches(self, mocked_cached_api):
        build_id = "some build id"
        version_id = "some version id"
        assert mocked_cached_api.build_by_id(build_id)
        assert mocked_cached_api.version_by_id(version_id)
        mocked_cached_api.clear_caches()
        assert mocked_cached_api.build_by_id(build_id)
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.session.request.call_count == 4


class TestRetryingEvergreenApi(object):
    def test_no_retries_on_success(self, mocked_retrying_api):
        version_id = "version id"

        mocked_retrying_api.version_by_id(version_id)
        assert mocked_retrying_api.session.request.call_count == 1

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    def test_three_retries_on_failure(self, mocked_retrying_api):
        version_id = "version id"
        mocked_retrying_api.session.request.side_effect = HTTPError()

        with pytest.raises(HTTPError):
            mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.request.call_count == under_test.MAX_RETRIES

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    def test_pass_on_retries_after_failure(self, mocked_retrying_api):
        version_id = "version id"
        successful_response = mocked_retrying_api.session.request.return_value
        mocked_retrying_api.session.request.side_effect = [HTTPError(), successful_response]

        mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.request.call_count == 2

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    def test_pass_on_retries_after_connection_error(self, mocked_retrying_api):
        version_id = "version id"
        successful_response = mocked_retrying_api.session.request.return_value

        mocked_retrying_api.session.request.side_effect = [
            requests.exceptions.ConnectionError(),
            successful_response,
        ]

        mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.request.call_count == 2

    def test_no_retries_on_non_http_errors(self, mocked_retrying_api):
        version_id = "version id"
        mocked_retrying_api.session.request.side_effect = ValueError("Unexpected Failure")

        with pytest.raises(ValueError):
            mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.request.call_count == 1
