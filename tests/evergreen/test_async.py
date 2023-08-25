import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from aiohttp.client_exceptions import ClientResponseError

import evergreen.async_api as under_test
from evergreen.api_requests import IssueLinkRequest, MetadataLinkRequest, SlackAttachment
from evergreen.config import DEFAULT_API_SERVER, DEFAULT_NETWORK_TIMEOUT_SEC
from evergreen.resource_type_permissions import PermissionableResourceType, RemovablePermission
from evergreen.util import EVG_DATETIME_FORMAT, parse_evergreen_datetime
from evergreen.version import Requester


def ns(relative):
    return "evergreen.async_api." + relative


def from_iso_format(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


class TestConfiguration(object):
    def test_uses_passed_auth(self, sample_evergreen_auth):
        kwargs = under_test.AsyncEvergreenApi._setup_kwargs(auth=sample_evergreen_auth)
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC

    @patch(ns("read_evergreen_config"))
    def test_uses_default_config_file(
        self, mock_read_evergreen_config, sample_evergreen_configuration, sample_evergreen_auth
    ):
        mock_read_evergreen_config.return_value = sample_evergreen_configuration
        kwargs = under_test.AsyncEvergreenApi._setup_kwargs(use_config_file=True)
        mock_read_evergreen_config.assert_called_once()
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC

    @patch(ns("read_evergreen_from_file"))
    def test_uses_passed_config_file(
        self, read_evergreen_from_file, sample_evergreen_configuration, sample_evergreen_auth
    ):
        read_evergreen_from_file.return_value = sample_evergreen_configuration
        kwargs = under_test.AsyncEvergreenApi._setup_kwargs(config_file="config.yml")
        read_evergreen_from_file.assert_called_once_with("config.yml")
        assert kwargs["auth"] == sample_evergreen_auth
        assert kwargs["timeout"] == DEFAULT_NETWORK_TIMEOUT_SEC


class TestRaiseForStatus(object):
    @pytest.mark.skipif(
        sys.version_info.major == 2, reason="JSONDecodeError is not used in python2"
    )
    @pytest.mark.asyncio
    async def test_non_json_error(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/versions/version_id")
        mock_aioresponse.get(expected_url, status=500, payload="TEST")
        with pytest.raises(ClientResponseError) as excinfo:
            await mocked_async_api.version_by_id("version_id")

        assert "Internal Server Error" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_json_errors_are_passed_through(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/versions/version_id")
        error_msg = "the error"
        mock_aioresponse.get(
            expected_url, status=500, payload={"error": error_msg},
        )

        with pytest.raises(ClientResponseError) as excinfo:
            await mocked_async_api.version_by_id("version_id")

        assert error_msg in str(excinfo.value)


class TestLazyPagination(object):
    @pytest.mark.asyncio
    async def test_with_no_next(self, mock_aioresponse, mocked_async_api):
        returned_items = ["item 1", "item 2", "item 3"]
        mock_aioresponse.get("http://url/?limit=100", status=200, payload=returned_items)

        result_count = 0
        async for result in mocked_async_api._async_lazy_paginate("http://url"):
            assert result in returned_items
            result_count += 1

        assert len(returned_items) == result_count

    @pytest.mark.asyncio
    async def test_next_in_response(self, mock_aioresponse, mocked_async_api):
        returned_items = ["item 1", "item 2", "item 3"]
        next_url = "<http://url_to_next>; rel='next'"
        mock_aioresponse.get(
            "http://url/?limit=100", status=200, payload=returned_items, headers={"Link": next_url}
        )
        mock_aioresponse.get(
            "http://url_to_next/?limit=100",
            status=200,
            payload=returned_items,
            headers={"Link": next_url},
        )
        mock_aioresponse.get(
            "http://url_to_next/?limit=100",
            status=200,
            payload=returned_items,
            headers={"Link": next_url},
        )
        mock_aioresponse.get(
            "http://url_to_next/?limit=100",
            status=200,
            payload=returned_items,
            headers={"Link": next_url},
        )

        items_to_check = len(returned_items) * 3
        i = 0
        async for result in mocked_async_api._async_lazy_paginate("http://url"):
            assert result in returned_items
            if i > items_to_check:
                break
            i += 1

        assert i > items_to_check


class TestSessions(object):
    @pytest.mark.asyncio
    async def test_session_can_be_created(self):
        evg_api = under_test.AsyncEvergreenApi()

        async with evg_api.async_session() as session_instance_one:
            async with evg_api.async_session() as session_instance_two:
                assert session_instance_one is not None
                assert session_instance_two is not None
                assert session_instance_one != session_instance_two

    @pytest.mark.asyncio
    async def test_with_session_creates_a_new_session(self):
        original_evg_api = under_test.AsyncEvergreenApi()

        async with original_evg_api.with_async_session() as evg_api_with_session:
            session_instance_one = evg_api_with_session.async_session
            session_instance_two = evg_api_with_session.async_session

            assert session_instance_one == session_instance_two
            assert original_evg_api._async_session != evg_api_with_session._async_session


class TestDistrosApi(object):
    @pytest.mark.asyncio
    async def test_all_distros(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/distros")
        mock_aioresponse.get(
            expected_url, status=200, payload=[{"name": "TEST", "arch": "TEST", "disabled": False}],
        )
        response = await mocked_async_api.all_distros()
        assert len(response) == 1
        assert response[0].name == "TEST"
        assert response[0].name == "TEST"
        assert not response[0].disabled


class TestHostApi(object):

    responses: List[Dict[str, Any]] = [{"status": "running"}, {"status": "success"}]

    @pytest.mark.asyncio
    async def test_all_hosts(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/hosts")
        mock_aioresponse.get(expected_url, status=200, payload=self.responses)
        response = await mocked_async_api.all_hosts()
        assert len(response) == 2
        assert response[0].status == "running"
        assert response[1].status == "success"

    @pytest.mark.asyncio
    async def test_all_hosts_with_status(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/hosts") + "?status=success"
        mock_aioresponse.get(
            expected_url, status=200, payload=self.responses[1:],
        )
        response = await mocked_async_api.all_hosts(status="success")
        assert len(response) == 1
        assert response[0].status == "success"


class TestProjectApi(object):

    projects: List[Dict[str, Any]] = [{"repo_name": "TEST"}]
    versions: List[Dict[str, Any]] = [{"version_id": "TEST"}]
    patches: List[Dict[str, Any]] = [{"patch_id": "TEST", "create_time": "2023-08-18"}]
    project_test_stats: List[Dict[str, Any]] = [{"test_file": "TEST"}]

    @pytest.mark.asyncio
    async def test_all_projects(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects")
        mock_aioresponse.get(
            expected_url, status=200, payload=self.projects,
        )
        response = await mocked_async_api.all_projects()
        assert len(response) == 1
        assert response[0].repo_name == "TEST"

    @pytest.mark.asyncio
    async def test_all_projects_with_filter(
        self, mock_aioresponse, mocked_async_api, sample_projects
    ):
        expected_url = mocked_async_api._create_url("/projects")
        mock_aioresponse.get(
            expected_url, status=200, payload=sample_projects,
        )

        def filter_fn(project):
            return project.identifier == "project 2"

        projects = await mocked_async_api.all_projects(filter_fn)

        assert len(projects) == 1
        assert projects[0].identifier == "project 2"
        assert projects[0].id == "project id 2"

    @pytest.mark.asyncio
    async def test_project_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects/project_id")
        mock_aioresponse.get(
            expected_url, status=200, payload=self.projects[0],
        )
        response = await mocked_async_api.project_by_id("project_id")
        assert response.repo_name == "TEST"

    @pytest.mark.asyncio
    async def test_recent_version_by_project(self, mock_aioresponse, mocked_async_api):
        recent_versions = {"rows": {"TEST": {"build_variant": "TEST"}}}
        expected_url = mocked_async_api._create_url("/projects/project_id/recent_versions")
        mock_aioresponse.get(
            expected_url, status=200, payload=recent_versions,
        )
        responses = await mocked_async_api.recent_versions_by_project("project_id")
        assert len(responses.rows) == 1
        assert responses.rows == recent_versions["rows"]

    @pytest.mark.asyncio
    async def test_version_by_project(self, mock_aioresponse, mocked_async_api):
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/versions")
            + "?requester=gitter_request"
        )
        mock_aioresponse.get(
            expected_url, status=200, payload=self.versions,
        )
        count = 0
        async for returned_version in mocked_async_api.versions_by_project("project_id"):
            count += 1
            assert returned_version.version_id == "TEST"
        assert count == 1

    @pytest.mark.asyncio
    async def test_version_by_project_with_limit_and_start(
        self, mock_aioresponse, mocked_async_api
    ):
        start = 15
        limit = 20
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/versions")
            + f"?limit={limit}&requester=gitter_request&start={start}"
        )
        mock_aioresponse.get(
            expected_url, status=200, payload=self.versions,
        )
        count = 0
        async for returned_version in mocked_async_api.versions_by_project(
            "project_id", start=start, limit=limit
        ):
            count += 1
            assert returned_version.version_id == "TEST"
        assert count == 1

    @pytest.mark.asyncio
    async def test_alias_for_version(self, mock_aioresponse, mocked_async_api):
        expected_url = (
            mocked_async_api._create_url("/projects/test_alias")
            + "?alias=my_alias&include_deps=false&version=version_id"
        )
        mock_aioresponse.get(
            expected_url, status=200, payload=[{"Variant": "TEST"}],
        )
        response = await mocked_async_api.alias_for_version("version_id", "my_alias")
        assert len(response) == 1
        assert response[0].variant == "TEST"

    @pytest.mark.asyncio
    async def test_versions_by_project_time_window(
        self, mock_aioresponse, mocked_async_api, sample_version
    ):
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

        expected_url = (
            mocked_async_api._create_url("/projects/project_id/versions")
            + "?requester=gitter_request"
        )
        mock_aioresponse.get(expected_url, status=200, payload=version_list)

        count = 0
        async for windowed_version in mocked_async_api.versions_by_project_time_window(
            "project_id", before_date, after_date
        ):
            count += 1
            assert version_list[1]["version_id"] == windowed_version.version_id
        assert count == 1

    @pytest.mark.asyncio
    async def test_patches_by_project(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects/project_id/patches") + "?limit=100"
        mock_aioresponse.get(expected_url, status=200, payload=self.patches)
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/patches")
            + "?limit=100&start_at=%25222023-08-18T00%253A00%253A00.000Z%2522"
        )
        mock_aioresponse.get(expected_url, status=200, payload="")
        count = 0
        async for patches in mocked_async_api.patches_by_project("project_id"):
            count += 1
            assert patches.patch_id == "TEST"
        assert count == 1

    @pytest.mark.asyncio
    async def test_patches_by_user(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/users/user_id/patches") + "?limit=100"
        mock_aioresponse.get(expected_url, status=200, payload=self.patches)
        expected_url = (
            mocked_async_api._create_url("/users/user_id/patches")
            + "?limit=100&start_at=%25222023-08-18T00%253A00%253A00.000Z%2522"
        )
        mock_aioresponse.get(expected_url, status=200, payload="")
        count = 0
        async for patches in mocked_async_api.patches_by_user("user_id"):
            count += 1
            assert patches.patch_id == "TEST"
        assert count == 1

    @pytest.mark.asyncio
    async def test_configure_patch(self, mock_aioresponse, mocked_async_api):
        variants = ["my_variant", ["*"]]
        description = "mypatch"
        expected_url = mocked_async_api._create_url("/patches/patch_id/configure")
        mock_aioresponse.post(expected_url, status=200)
        await mocked_async_api.configure_patch(
            "patch_id", description=description, variants=variants
        )

    @pytest.mark.asyncio
    async def test_configure_patch_variants(self, mock_aioresponse, mocked_async_api):
        variants = ["my_variant", ["task_one", "task_two"]]
        expected_url = mocked_async_api._create_url("/patches/patch_id/configure")
        mock_aioresponse.post(expected_url, status=200)
        await mocked_async_api.configure_patch("patch_id", variants=variants)

    @pytest.mark.asyncio
    async def test_patches_by_project_time_window(
        self, mock_aioresponse, mocked_async_api, sample_patch
    ):
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

        expected_url = mocked_async_api._create_url("/projects/project_id/patches") + "?limit=100"
        mock_aioresponse.get(expected_url, status=200, payload=patch_list)

        count = 0
        async for patches in mocked_async_api.patches_by_project_time_window(
            "project_id", before_date, after_date
        ):
            count += 1
            assert patch_list[1]["patch_id"] == patches.patch_id
        assert count == 1

    @pytest.mark.asyncio
    async def test_commit_queue_for_project(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/commit_queue/project_id")
        mock_aioresponse.get(expected_url, status=200, payload={"queue_id": "TEST"})
        response = await mocked_async_api.commit_queue_for_project("project_id")
        assert response.queue_id == "TEST"

    @pytest.mark.asyncio
    async def test_test_stats_by_project(self, mock_aioresponse, mocked_async_api):
        after_date = "2019-01-01"
        before_date = "2019-02-01"
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/test_stats")
            + f"?after_date={after_date}&before_date={before_date}"
        )

        mock_aioresponse.get(expected_url, status=200, payload=self.project_test_stats)

        response = await mocked_async_api.test_stats_by_project(
            "project_id", from_iso_format(after_date), from_iso_format(before_date),
        )
        assert response[0].test_file == "TEST"

    @pytest.mark.asyncio
    async def test_test_stats_by_project_with_requester(self, mock_aioresponse, mocked_async_api):
        after_date = "2019-01-01"
        before_date = "2019-02-01"
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/test_stats")
            + f"?after_date={after_date}&before_date={before_date}&requesters=patch"
        )

        mock_aioresponse.get(expected_url, status=200, payload=self.project_test_stats)

        response = await mocked_async_api.test_stats_by_project(
            "project_id",
            from_iso_format(after_date),
            from_iso_format(before_date),
            requesters=Requester.PATCH_REQUEST,
        )
        assert response[0].test_file == "TEST"

    @pytest.mark.asyncio
    async def test_single_test_by_task(self, mock_aioresponse, mocked_async_api):
        expected_url = (
            mocked_async_api._create_url("/tasks/task_id/tests")
            + "?test_name=com.xgen.module.MyTests.test1"
        )

        mock_aioresponse.get(expected_url, status=200, payload=[{"test_file": "TEST"}])
        response = await mocked_async_api.single_test_by_task_and_test_file(
            "task_id", "com.xgen.module.MyTests.test1"
        )
        assert response[0].test_file == "TEST"

    @pytest.mark.asyncio
    async def test_send_slack_message(self, mock_aioresponse, mocked_async_api):
        target = "@fake-user"
        msg = "I'm a fake message"
        expected_url = mocked_async_api._create_url("/notifications/slack")

        mock_aioresponse.post(expected_url, status=200, payload={"TEST": "TEST"})

        await mocked_async_api.send_slack_message(target, msg)

    @pytest.mark.asyncio
    async def test_send_slack_message_with_attachments(self, mock_aioresponse, mocked_async_api):
        target = "@fake-user"
        msg = "I'm a fake message"
        attachments = [
            SlackAttachment(text="Test Text", title="Test Title"),
            SlackAttachment(text="Fake text", title="Fake title"),
        ]
        expected_url = mocked_async_api._create_url("/notifications/slack")

        mock_aioresponse.post(expected_url, status=200, payload={"TEST": "TEST"})
        await mocked_async_api.send_slack_message(target, msg, attachments)

    @pytest.mark.asyncio
    async def test_tasks_by_project(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects/project_id/versions/tasks")

        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])

        response = await mocked_async_api.tasks_by_project("project_id")
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tasks_by_project_with_statuses(self, mock_aioresponse, mocked_async_api):
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/versions/tasks") + "?status=status1"
        )

        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tasks_by_project("project_id", statuses=["status1"])
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tasks_by_project_and_name(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects/project_id/tasks/task_name")

        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tasks_by_project_and_name("project_id", "task_name")
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tasks_by_project_and_name_with_data(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/projects/project_id/tasks/task_name")

        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tasks_by_project_and_name(
            "project_id", "task_name", build_variant="build_variant", num_versions=50, start_at=10
        )
        assert response[0].task_id == "TEST"


class TestTaskStatsByProject(object):
    @pytest.mark.asyncio
    async def test_with_multiple_tasks(self, mock_aioresponse, mocked_async_api):
        after_date = "2020-04-04"
        before_date = "2020-05-04"
        task_list = [f"task_{i}" for i in range(3)]
        expected_url = (
            mocked_async_api._create_url("/projects/project_id/task_stats")
            + f"?after_date={after_date}&before_date={before_date}&tasks={'&tasks='.join(task_list)}"
        )
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])

        response = await mocked_async_api.task_stats_by_project(
            "project_id",
            after_date=from_iso_format(after_date),
            before_date=from_iso_format(before_date),
            tasks=task_list,
        )
        assert response[0].task_id == "TEST"


class TestBuildApi(object):
    @pytest.mark.asyncio
    async def test_build_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/builds/build_id")
        mock_aioresponse.get(expected_url, status=200, payload={"task_id": "TEST"})
        response = await mocked_async_api.build_by_id("build_id")
        assert response.task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tasks_by_build(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/builds/build_id/tasks")
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tasks_by_build("build_id")
        assert response[0].task_id == "TEST"


class TestVersionApi(object):
    @pytest.mark.asyncio
    async def test_version_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/versions/version_id")
        mock_aioresponse.get(expected_url, status=200, payload={"version_id": "TEST"})
        response = await mocked_async_api.version_by_id("version_id")
        assert response.version_id == "TEST"

    @pytest.mark.asyncio
    async def test_builds_by_version(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/versions/version_id/builds")
        mock_aioresponse.get(expected_url, status=200, payload=[{"_id": "TEST"}])
        response = await mocked_async_api.builds_by_version("version_id")
        assert response[0].id == "TEST"


class TestPatchApi(object):
    @pytest.mark.asyncio
    async def test_patch_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/patches/patch_id")
        mock_aioresponse.get(
            expected_url, status=200, payload={"patch_id": "TEST", "description": "TEST"}
        )
        response = await mocked_async_api.patch_by_id("patch_id")
        assert response.patch_id == "TEST"
        assert response.description == "TEST"

    @pytest.mark.asyncio
    async def test_update_patch_activate(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/patches/patch_id")
        mock_aioresponse.patch(expected_url, status=200, payload=[{"_id": "TEST"}])
        await mocked_async_api.update_patch_status("patch_id", activated=True)

    @pytest.mark.asyncio
    async def test_update_patch_priority(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/patches/patch_id")
        mock_aioresponse.patch(expected_url, status=200, payload=[{"_id": "TEST"}])
        await mocked_async_api.update_patch_status("patch_id", priority=100)

    @pytest.mark.asyncio
    async def test_update_patch(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/patches/patch_id")
        mock_aioresponse.patch(expected_url, status=200, payload=[{"_id": "TEST"}])
        await mocked_async_api.update_patch_status("patch_id", priority=100, activated=True)

    @pytest.mark.asyncio
    async def test_patch_diff_api(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/patches/patch_id/raw")
        mock_aioresponse.get(expected_url, status=200, body="TEST")
        response = await mocked_async_api.get_patch_diff("patch_id")
        assert response == "TEST"


class TestCreatePatchDiff:
    @pytest.mark.asyncio
    async def test_patch_from_diff_valid_no_author(self, fp, mocked_async_api):
        fp.register(
            "evergreen patch-file --diff-file path --description 'description' --param params --base base --tasks task --variants variant --project project -y -f",
            stderr=b"[evergreen] 2023/04/13 15:05:24 [p=info]: Patch successfully created.\n[evergreen] 2023/04/13 15:05:24 [p=info]: \n         ID : 64387ca457e85ac95a3da12f\n    Created : 2023-04-13 22:05:24.463 +0000 UTC\n    Description : Test enable profiling.\n      Build : https://evergreen.mongodb.com/patch/64387ca457e85ac95a3da12f?redirect_spruce_users=true\n     Status : created\n\n\n",
        )

        result = await mocked_async_api.patch_from_diff(
            "path", "params", "base", "task", "project", "description", "variant"
        )

        assert (
            result.url
            == "https://evergreen.mongodb.com/patch/64387ca457e85ac95a3da12f?redirect_spruce_users=true"
        )

    @pytest.mark.asyncio
    async def test_patch_from_diff_valid_with_author(self, fp, mocked_async_api):
        fp.register(
            "evergreen patch-file --diff-file path --description 'description' --param params --base base --tasks task --variants variant --project project -y -f --author author",
            stderr=b"[evergreen] 2023/04/13 15:05:24 [p=info]: Patch successfully created.\n[evergreen] 2023/04/13 15:05:24 [p=info]: \n         ID : 64387ca457e85ac95a3da12f\n    Created : 2023-04-13 22:05:24.463 +0000 UTC\n    Description : Test enable profiling.\n      Build : https://evergreen.mongodb.com/patch/64387ca457e85ac95a3da12f?redirect_spruce_users=true\n     Status : created\n\n\n",
        )

        result = await mocked_async_api.patch_from_diff(
            "path", "params", "base", "task", "project", "description", "variant", "author"
        )
        assert (
            result.url
            == "https://evergreen.mongodb.com/patch/64387ca457e85ac95a3da12f?redirect_spruce_users=true"
        )

    @pytest.mark.asyncio
    async def test_patch_from_diff_invalid(self, fp, mocked_async_api):
        fp.register(
            "evergreen patch-file --diff-file path --description 'description' --param params --base base --tasks task --variants variant --project project -y -f",
            stderr=b"no url here",
        )

        with pytest.raises(Exception) as e:
            await mocked_async_api.patch_from_diff(
                "path", "params", "base", "task", "project", "description", "variant"
            )
            assert "Unable to parse URL from command output: " in e


class TestTaskApi(object):
    @pytest.mark.asyncio
    async def test_task_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id")
        mock_aioresponse.get(expected_url, status=200, payload={"task_id": "TEST"})
        response = await mocked_async_api.task_by_id("task_id")
        assert response.task_id == "TEST"

    @pytest.mark.asyncio
    async def test_task_by_id_with_fetch_executions(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id") + "?fetch_all_executions=true"
        mock_aioresponse.get(expected_url, status=200, payload={"task_id": "TEST"})
        response = await mocked_async_api.task_by_id("task_id", fetch_all_executions=True)
        assert response.task_id == "TEST"

    @pytest.mark.asyncio
    async def test_manifest_for_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/manifest")
        mock_aioresponse.get(expected_url, status=200, payload={"id": "TEST"})
        response = await mocked_async_api.manifest_for_task("task_id")
        assert response.id == "TEST"

    @pytest.mark.asyncio
    async def test_manifest_for_task_does_not_exist(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/manifest")
        mock_aioresponse.get(expected_url, status=HTTPStatus.NOT_FOUND, payload="")
        response = await mocked_async_api.manifest_for_task("task_id")
        assert response is None

    @pytest.mark.asyncio
    async def test_manifest_for_task_throws_exception(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/manifest")
        mock_aioresponse.get(expected_url, status=500, payload="")

        with pytest.raises(ClientResponseError) as _:
            await mocked_async_api.manifest_for_task("task_id")

    @pytest.mark.asyncio
    async def test_tests_by_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/tests")
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tests_by_task("task_id")
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tests_by_task_with_status(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/tests") + "?status=success"
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tests_by_task("task_id", status="success")
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tests_by_task_with_execution(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/tests") + "?execution=5"
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tests_by_task("task_id", execution=5)
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_tests_by_task_with_status_and_execution(
        self, mock_aioresponse, mocked_async_api
    ):
        expected_url = (
            mocked_async_api._create_url("/tasks/task_id/tests") + "?execution=5&status=success"
        )
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.tests_by_task("task_id", status="success", execution=5)
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_num_of_tests_by_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/tests/count")
        mock_aioresponse.get(expected_url, status=200, body="1")
        response = await mocked_async_api.num_of_tests_by_task("task_id")
        assert response == 1

    @pytest.mark.asyncio
    async def test_get_task_annotation(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/annotations") + "?execution=5"
        mock_aioresponse.get(expected_url, status=200, body=json.dumps([{"task_id": "TEST"}]))
        response = await mocked_async_api.get_task_annotation("task_id", execution=5)
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_get_task_annotation_with_invalid_parameters(self, mocked_async_api):
        with pytest.raises(ValueError):
            await mocked_async_api.get_task_annotation(
                "task_id", execution=5, fetch_all_executions=True
            )

    @pytest.mark.asyncio
    async def test_file_ticket(self, mock_aioresponse, mocked_async_api):
        expected_url = (
            mocked_async_api._create_url("/tasks/task_id_3/created_ticket") + "?execution=5"
        )
        mock_aioresponse.put(expected_url, status=200)
        await mocked_async_api.file_ticket_for_task(
            task_id="task_id_3",
            execution=5,
            ticket_link="https://google.com",
            ticket_key="fake-key",
        )

    @pytest.mark.asyncio
    async def test_annotate_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/annotation")
        mock_aioresponse.put(expected_url, status=200)
        await mocked_async_api.annotate_task(
            "task_id",
            message="hello world",
            issues=[IssueLinkRequest(issue_key="key-1234", url="http://hello.world/key-1234")],
            metadata_links=[MetadataLinkRequest(url="https://www.mongodb.com", text="mongodb")],
        )

    @pytest.mark.asyncio
    async def test_annotate_task_with_zero_execution(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/annotation")
        mock_aioresponse.put(expected_url, status=200)
        await mocked_async_api.annotate_task(
            "task_id",
            execution=0,
            message="hello world",
            issues=[IssueLinkRequest(issue_key="key-1234", url="http://hello.world/key-1234")],
        )

    @pytest.mark.asyncio
    async def test_performance_results_by_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_plugin_url("/task/task_id/perf")
        mock_aioresponse.get(expected_url, status=200, payload={"task_id": "TEST"})
        response = await mocked_async_api.performance_results_by_task("task_id")
        assert response.task_id == "TEST"

    @pytest.mark.asyncio
    async def test_performance_results_by_task_name(self, mock_aioresponse, mocked_async_api):
        expected_url = "{api_server}/api/2/task/task_id/json/history/task_name/perf".format(
            api_server=DEFAULT_API_SERVER
        )
        mock_aioresponse.get(expected_url, status=200, payload=[{"task_id": "TEST"}])
        response = await mocked_async_api.performance_results_by_task_name("task_id", "task_name")
        assert response[0].task_id == "TEST"

    @pytest.mark.asyncio
    async def test_json_by_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_plugin_url("/task/task_id/json_key_id")
        mock_aioresponse.get(expected_url, status=200, payload={"TEST": "TEST"})
        response = await mocked_async_api.json_by_task("task_id", "json_key_id")
        assert response["TEST"] == "TEST"

    @pytest.mark.asyncio
    async def test_json_history_for_task(self, mock_aioresponse, mocked_async_api):
        expected_url = f"{DEFAULT_API_SERVER}/api/2/task/task_id/json/history/task_name/json_key_id"
        mock_aioresponse.get(expected_url, status=200, payload={"TEST": "TEST"})
        response = await mocked_async_api.json_history_for_task(
            "task_id", "task_name", "json_key_id"
        )
        assert response["TEST"] == "TEST"

    @pytest.mark.asyncio
    async def test_restart_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/restart")
        mock_aioresponse.post(expected_url, status=200)
        await mocked_async_api.restart_task("task_id")

    @pytest.mark.asyncio
    async def test_abort_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id/abort")
        mock_aioresponse.post(expected_url, status=200)
        await mocked_async_api.abort_task("task_id")

    @pytest.mark.asyncio
    async def test_configure_task_activate(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id")
        mock_aioresponse.patch(expected_url, status=200)
        await mocked_async_api.configure_task("task_id", activated=True)

    @pytest.mark.asyncio
    async def test_configure_task_priority(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id")
        mock_aioresponse.patch(expected_url, status=200)
        await mocked_async_api.configure_task("task_id", priority=100)

    @pytest.mark.asyncio
    async def test_configure_task(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/tasks/task_id")
        mock_aioresponse.patch(expected_url, status=200)
        await mocked_async_api.configure_task("task_id", priority=100, activated=True)


class TestOldApi(object):
    @pytest.mark.asyncio
    async def test_patch_by_id(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_old_url("plugin/manifest/get/project_id/revision")
        mock_aioresponse.get(expected_url, status=200, payload={"id": "TEST"})
        response = await mocked_async_api.manifest("project_id", "revision")
        assert response.id == "TEST"


class TestLogApi(object):
    @pytest.mark.asyncio
    async def test_retrieve_log(self, mock_aioresponse, mocked_async_api):
        mock_aioresponse.get("log_url", status=200, body="TEST")
        response = await mocked_async_api.retrieve_task_log("log_url")
        assert response == "TEST"

    @pytest.mark.asyncio
    async def test_retrieve_log_with_raw(self, mock_aioresponse, mocked_async_api):
        mock_aioresponse.get("log_url?text=true", status=200, body="TEST")
        response = await mocked_async_api.retrieve_task_log("log_url", raw=True)
        assert response == "TEST"

    @pytest.mark.asyncio
    async def test_stream_log(self, mock_aioresponse, mocked_async_api):
        streamed_data = "\n".join(["line_{}".format(i) for i in range(10)])
        mock_aioresponse.get("log_url?text=true", status=200, body=streamed_data)

        async for line in mocked_async_api.stream_log("log_url"):
            assert line in streamed_data


class TestUserPermissionsApi(object):
    @pytest.mark.asyncio
    async def test_permissions_for_user(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/users/test.user/permissions")
        permissions = [{"type": "project", "permissions": {"proj1": {"test": 1}}}]
        mock_aioresponse.get(expected_url, status=200, payload=permissions)
        returned_permissions = await mocked_async_api.permissions_for_user("test.user")
        assert len(returned_permissions) == 1
        assert returned_permissions[0].resource_type == "project"
        assert returned_permissions[0].permissions == permissions[0]["permissions"]

    @pytest.mark.asyncio
    async def test_give_permissions_to_user(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/users/test.user/permissions")
        mock_aioresponse.post(expected_url, status=200)
        resources = ["resource-1", "resource-2"]
        permissions = {"proj1": {"test": 1}}
        await mocked_async_api.give_permissions_to_user(
            "test.user", PermissionableResourceType.PROJECT, resources, permissions
        )

    @pytest.mark.asyncio
    async def test_delete_user_permissions_all_resources(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/users/test.user/permissions")
        mock_aioresponse.delete(expected_url, status=200)
        await mocked_async_api.delete_user_permissions("test.user", RemovablePermission.PROJECT)

    @pytest.mark.asyncio
    async def test_delete_user_permissions_specific_resource(
        self, mock_aioresponse, mocked_async_api
    ):
        expected_url = mocked_async_api._create_url("/users/test.user/permissions")
        mock_aioresponse.delete(expected_url, status=200)
        await mocked_async_api.delete_user_permissions(
            "test.user", RemovablePermission.PROJECT, "testresource"
        )

    @pytest.mark.asyncio
    async def test_all_user_permissions_for_resource(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/users/permissions")
        permissions = {"user1": {"project_tasks": 10, "project_patches": 10}}
        mock_aioresponse.get(expected_url, status=200, payload=permissions)
        returned_permissions = await mocked_async_api.all_user_permissions_for_resource(
            "resource-1", PermissionableResourceType.PROJECT
        )
        assert returned_permissions == permissions


class TestRolesApi(object):
    @pytest.mark.parametrize("create_user", [False, True])
    @pytest.mark.asyncio
    async def test_give_roles_to_user(self, mock_aioresponse, mocked_async_api, create_user):
        expected_url = mocked_async_api._create_url("/users/test.user/roles")
        mock_aioresponse.post(expected_url, status=200)
        roles = ["role1", "role2"]
        await mocked_async_api.give_roles_to_user("test.user", roles, create_user)

    @pytest.mark.asyncio
    async def test_get_users_for_role(self, mock_aioresponse, mocked_async_api):
        expected_url = mocked_async_api._create_url("/roles/testrole/users")
        users = ["test1", "test2", "test3"]
        mock_aioresponse.get(expected_url, status=200, payload={"users": users})
        returned_response = await mocked_async_api.get_users_for_role("testrole")
        assert returned_response.users == users


class TestRetryingAsyncEvergreenApi(object):
    @pytest.mark.asyncio
    async def test_no_retries_on_success(self, mock_aioresponse, mocked_async_retrying_api):
        expected_url = mocked_async_retrying_api._create_url("/versions/version%20id")
        mock_aioresponse.get(expected_url, status=200, payload={"version_id": "TEST"})

        version_id = "version id"
        response = await mocked_async_retrying_api.version_by_id(version_id)
        assert response.version_id == "TEST"

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    @pytest.mark.asyncio
    async def test_three_retries_on_failure(self, mock_aioresponse, mocked_async_retrying_api):
        version_id = "version id"
        expected_url = mocked_async_retrying_api._create_url("/versions/version%20id")
        mock_aioresponse.get(expected_url, status=500, payload="", repeat=True)

        with pytest.raises(ClientResponseError):
            await mocked_async_retrying_api.version_by_id(version_id)

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    @pytest.mark.asyncio
    async def test_pass_on_retries_after_failure(self, mock_aioresponse, mocked_async_retrying_api):
        version_id = "version id"
        expected_url = mocked_async_retrying_api._create_url("/versions/version%20id")
        mock_aioresponse.get(expected_url, status=500, payload="")
        mock_aioresponse.get(expected_url, status=200, payload={"version_id": "TEST"})
        response = await mocked_async_retrying_api.version_by_id(version_id)
        assert response.version_id == "TEST"

    @pytest.mark.skipif(
        not os.environ.get("RUN_SLOW_TESTS"), reason="Slow running test due to retries"
    )
    @pytest.mark.asyncio
    async def test_pass_on_retries_after_connection_error(
        self, mock_aioresponse, mocked_async_retrying_api
    ):
        version_id = "version id"
        expected_url = mocked_async_retrying_api._create_url("/versions/version%20id")
        mock_aioresponse.get(expected_url, status=500, payload="")
        mock_aioresponse.get(expected_url, status=200, payload={"version_id": "TEST"})
        response = await mocked_async_retrying_api.version_by_id(version_id)
        assert response.version_id == "TEST"

    @pytest.mark.asyncio
    async def test_no_retries_on_non_http_errors(self, mock_aioresponse, mocked_async_retrying_api):
        expected_url = mocked_async_retrying_api._create_url("/versions/version%20id")
        mock_aioresponse.get(expected_url, status=500, payload="", repeat=True)

        with pytest.raises(ClientResponseError):
            version_id = "version id"
            await mocked_async_retrying_api.version_by_id(version_id)
