# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from evergreen.task import (
    _EVG_DATE_FIELDS_IN_TASK,
    EVG_TEST_STATUS_TYPE,
    OomTrackerInfo,
    StatusScore,
    Task,
)


class TestTask(object):
    def test_evg_task_has_no_estimated_cost(self, sample_task):
        assert not sample_task.get("estimated_cost")
        task = Task(sample_task, None)
        with pytest.raises(AttributeError):
            assert task.estimated_cost

    def test_task_has_oom(self, sample_task):
        task = Task(sample_task, None)
        assert task.has_oom()

    def test_task_does_not_have_oom(self, sample_task):
        sample_task["status_details"]["oom_tracker_info"]["detected"] = False
        task = Task(sample_task, None)
        assert not task.has_oom()

    def test_task_has_pids(self, sample_task):
        task = Task(sample_task, None)
        assert task.get_oom_pids() == [19803]

    def test_task_does_not_have_pids(self, sample_task):
        sample_task["status_details"]["oom_tracker_info"]["pids"] = None
        task = Task(sample_task, None)
        assert task.get_oom_pids() == []

    def test_oom_tracker_info_object_has_oom(self, sample_task):
        task = Task(sample_task, None)
        assert task.status_details.oom_tracker_info == OomTrackerInfo(
            task.json["status_details"]["oom_tracker_info"], None
        )
        assert (
            task.status_details.oom_tracker_info.detected
            == task.status_details.json["oom_tracker_info"]["detected"]
        )
        assert (
            task.status_details.oom_tracker_info.pids
            == task.status_details.json["oom_tracker_info"]["pids"]
        )

    def test_oom_tracker_info_object_does_not_have_oom(self, sample_task):
        sample_task["status_details"]["oom_tracker_info"]["detected"] = False
        sample_task["status_details"]["oom_tracker_info"]["pids"] = None
        task = Task(sample_task, None)
        assert task.status_details.oom_tracker_info == OomTrackerInfo(
            task.json["status_details"]["oom_tracker_info"], None
        )
        assert (
            task.status_details.oom_tracker_info.detected
            == task.status_details.json["oom_tracker_info"]["detected"]
        )
        assert (
            task.status_details.oom_tracker_info.pids
            == task.status_details.json["oom_tracker_info"]["pids"]
        )

    def test_time_fields_return_time_objects(self, sample_task):
        task = Task(sample_task, None)
        for date_field in _EVG_DATE_FIELDS_IN_TASK:
            assert isinstance(getattr(task, date_field), datetime)

    def test_getting_attributes(self, sample_task):
        task = Task(sample_task, None)
        assert sample_task["task_id"] == task.task_id
        with pytest.raises(AttributeError):
            task.not_really_an_attribute

    def test_status_attributes(self, sample_task):
        task = Task(sample_task, None)
        assert task.is_success()
        assert not task.is_system_failure()
        assert not task.is_timeout()
        assert not task.is_test_failure()

    def test_bad_status_attributes(self, sample_task):
        sample_task["status_details"]["type"] = "system"
        sample_task["status"] = "failed"
        sample_task["status_details"]["timed_out"] = True
        task = Task(sample_task, None)
        assert not task.is_success()
        assert task.is_system_failure()
        assert task.is_timeout()

    def test_task_is_test_failure(self, sample_task):
        sample_task["status_details"]["type"] = EVG_TEST_STATUS_TYPE
        sample_task["status"] = "failed"
        task = Task(sample_task, None)
        assert not task.is_success()
        assert not task.is_system_failure()
        assert not task.is_timeout()
        assert task.is_test_failure()

    def test_wait_time(self, sample_task):
        task = Task(sample_task, None)
        assert timedelta(minutes=30) == task.wait_time()

    def test_missing_wait_time(self, sample_task):
        sample_task["start_time"] = None
        task = Task(sample_task, None)
        assert not task.wait_time()

    def test_wait_time_once_unblocked(self, sample_task):
        task = Task(sample_task, None)
        assert timedelta(minutes=20) == task.wait_time_once_unblocked()

    def test_missing_wait_time_once_unblocked(self, sample_task):
        sample_task["scheduled_time"] = None
        task = Task(sample_task, None)
        assert not task.wait_time_once_unblocked()

    def test_get_execution(self, sample_task):
        task = Task(sample_task, None)
        execution1 = task.get_execution(1)
        assert execution1.display_name == "aggregation_auth"

        execution0 = task.get_execution(0)
        assert execution0.display_name == "sharding_auth_gen"

        assert not task.get_execution(999)

    def test_get_execution_or_self(self, sample_task):
        task = Task(sample_task, None)
        execution = task.get_execution_or_self(0)

        assert execution.display_name == "sharding_auth_gen"

    def test_get_execution_or_self_with_no_execution(self, sample_task):
        task = Task(sample_task, None)
        execution = task.get_execution_or_self(999)

        assert execution == task

    def test_artifacts(self, sample_task):
        task = Task(sample_task, None)
        assert len(task.artifacts) == len(sample_task["artifacts"])
        assert task.artifacts[0].name == sample_task["artifacts"][0]["name"]

    def test_no_artifacts(self, sample_task):
        sample_task["artifacts"] = None
        task = Task(sample_task, None)
        assert len(task.artifacts) == 0

    def test_logs(self, sample_task):
        task = Task(sample_task, None)

        assert isinstance(task.log_map, dict)
        assert task.log_map["all_log"] == sample_task["logs"]["all_log"]

    def test_retrieve_log(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        log = task.retrieve_log("task_log")
        assert log == mock_api.retrieve_task_log.return_value

    def test_get_project_identifier(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        identifier = task.get_project_identifier()
        assert identifier == mock_api.project_by_id(task.project_id).identifier

    def test_retrieve_log_with_raw(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        log = task.retrieve_log("task_log", raw=True)
        assert log == mock_api.retrieve_task_log.return_value
        mock_api.retrieve_task_log.assert_called_with(task.log_map["task_log"], True)

    def test_stream_log(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        log = task.stream_log("task_log")
        assert log == mock_api.stream_log.return_value

    def test_successful_task_is_not_undispatched(self, sample_task):
        sample_task["status"] = "success"
        task = Task(sample_task, None)

        assert not task.is_undispatched()

    def test_undispatched_task_is_undispatched(self, sample_task):
        sample_task["status"] = "undispatched"
        task = Task(sample_task, None)

        assert task.is_undispatched()

    def test_active_task(self, sample_task):
        sample_task["finish_time"] = None
        task = Task(sample_task, None)

        assert task.is_active()

    def test_inactive_task_not_scheduled(self, sample_task):
        sample_task["finish_time"] = None
        sample_task["scheduled_time"] = None
        task = Task(sample_task, None)

        assert not task.is_active()

    def test_inactive_task_finished(self, sample_task):
        task = Task(sample_task, None)

        assert not task.is_active()

    @pytest.mark.parametrize(
        "execution,expected", [(None, 1), (0, 0)],
    )
    def test_get_tests(self, sample_task, execution, expected):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)

        if execution is None:
            tests = task.get_tests()
        else:
            tests = task.get_tests(execution=execution)

        mock_api.tests_by_task.assert_called_once()

        kwargs = mock_api.tests_by_task.call_args[1]
        assert "execution" in kwargs and kwargs["execution"] == expected
        assert tests == mock_api.tests_by_task.return_value

    @pytest.mark.parametrize(
        "status_string,status_score",
        [
            ("success", StatusScore.SUCCESS),
            ("failure", StatusScore.FAILURE),
            ("undispatched", StatusScore.UNDISPATCHED),
        ],
    )
    def test_no_details_task_is_scored_correctly(self, sample_task, status_string, status_score):
        sample_task["status"] = status_string
        task = Task(sample_task, None)

        assert task.get_status_score() == status_score

    @pytest.mark.parametrize(
        "status_string,status_score",
        [(True, StatusScore.FAILURE_TIMEOUT), (False, StatusScore.FAILURE_SYSTEM)],
    )
    def test_detailed_task_is_scored_correctly(self, sample_task, status_string, status_score):
        sample_task["status_details"]["type"] = "system"
        sample_task["status"] = "failed"
        sample_task["status_details"]["timed_out"] = status_string
        task = Task(sample_task, None)

        assert task.get_status_score() == status_score

    def test_get_execution_tasks(self, sample_task, sample_display_task):
        mock_api = MagicMock()
        mock_api.task_by_id.return_value = Task(sample_task, mock_api)

        display_task = Task(sample_display_task, mock_api)
        execution_tasks = display_task.get_execution_tasks()

        assert len(execution_tasks) == len(sample_display_task["execution_tasks"])

    def test_get_execution_tasks_with_filters(self, sample_task, sample_display_task):
        mock_api = MagicMock()
        mock_api.task_by_id.return_value = Task(sample_task, mock_api)
        max_return = 2
        seen = 0

        def cap_seen(t):
            nonlocal seen
            if seen >= max_return:
                return False
            seen += 1
            return True

        display_task = Task(sample_display_task, mock_api)
        execution_tasks = display_task.get_execution_tasks(filter_fn=cap_seen)

        assert len(execution_tasks) == max_return

    def test_get_manifest(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)

        manifest = task.get_manifest()

        assert manifest == mock_api.manifest_for_task.return_value
        mock_api.manifest_for_task.assert_called_with(task.task_id)
