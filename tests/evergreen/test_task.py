# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta

import pytest

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from evergreen.task import Task, _EVG_DATE_FIELDS_IN_TASK


class TestTask(object):
    def test_time_fields_return_time_objects(self, sample_task):
        task = Task(sample_task, None)
        for date_field in _EVG_DATE_FIELDS_IN_TASK:
            assert isinstance(getattr(task, date_field), datetime)

    def test_getting_attributes(self, sample_task):
        task = Task(sample_task, None)
        assert sample_task['task_id'] == task.task_id
        with pytest.raises(AttributeError):
            task.not_really_an_attribute

    def test_status_attributes(self, sample_task):
        task = Task(sample_task, None)
        assert task.is_success()
        assert not task.is_system_failure()
        assert not task.is_timeout()

    def test_bad_status_attributes(self, sample_task):
        sample_task['status_details']['type'] = 'system'
        sample_task['status'] = 'failed'
        sample_task['status_details']['timed_out'] = True
        task = Task(sample_task, None)
        assert not task.is_success()
        assert task.is_system_failure()
        assert task.is_timeout()

    def test_wait_time(self, sample_task):
        task = Task(sample_task, None)
        assert timedelta(minutes=30) == task.wait_time()

    def test_missing_wait_time(self, sample_task):
        sample_task['start_time'] = None
        task = Task(sample_task, None)
        assert not task.wait_time()

    def test_wait_time_once_unblocked(self, sample_task):
        task = Task(sample_task, None)
        assert timedelta(minutes=20) == task.wait_time_once_unblocked()

    def test_missing_wait_time_once_unblocked(self, sample_task):
        sample_task['scheduled_time'] = None
        task = Task(sample_task, None)
        assert not task.wait_time_once_unblocked()

    def test_get_execution(self, sample_task):
        task = Task(sample_task, None)
        execution1 = task.get_execution(1)
        assert execution1.display_name == 'aggregation_auth'

        execution0 = task.get_execution(0)
        assert execution0.display_name == 'sharding_auth_gen'

        assert not task.get_execution(999)

    def test_artifacts(self, sample_task):
        task = Task(sample_task, None)
        assert len(task.artifacts) == len(sample_task['artifacts'])
        assert task.artifacts[0].name == sample_task['artifacts'][0]['name']

    def test_logs(self, sample_task):
        task = Task(sample_task, None)

        assert isinstance(task.log_map, dict)
        assert task.log_map['all_log'] == sample_task['logs']['all_log']

    def test_retrieve_log(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        log = task.retrieve_log('task_log')
        assert log == mock_api.retrieve_task_log.return_value

    def test_retrieve_log_with_raw(self, sample_task):
        mock_api = MagicMock()
        task = Task(sample_task, mock_api)
        log = task.retrieve_log('task_log', raw=True)
        assert log == mock_api.retrieve_task_log.return_value
        mock_api.retrieve_task_log.assert_called_with(task.log_map['task_log'], True)

    def test_successful_task_is_not_undispatched(self, sample_task):
        sample_task['status'] = 'success'
        task = Task(sample_task, None)

        assert not task.is_undispatched()

    def test_undispatched_task_is_undispatched(self, sample_task):
        sample_task['status'] = 'undispatched'
        task = Task(sample_task, None)

        assert task.is_undispatched()

    def test_active_task(self, sample_task):
        sample_task['finish_time'] = None
        task = Task(sample_task, None)

        assert task.is_active()

    def test_inactive_task_not_scheduled(self, sample_task):
        sample_task['finish_time'] = None
        sample_task['scheduled_time'] = None
        task = Task(sample_task, None)

        assert not task.is_active()

    def test_inactive_task_finished(self, sample_task):
        task = Task(sample_task, None)

        assert not task.is_active()
