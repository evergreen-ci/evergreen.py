import os
import sys

from evergreen.config import DEFAULT_API_SERVER, EvgAuth, DEFAULT_NETWORK_TIMEOUT_SEC

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError
from tenacity import RetryError

import evergreen.api as under_test
from evergreen.api import EvergreenApi

try:
    from json.decoder import JSONDecodeError
except ImportError:  # This doesn't exist in python 2.
    pass


def ns(relative):
    return "evergreen.api." + relative


class TestConfiguration(object):
    def test_uses_passed_auth(self, sample_evergreen_auth):
        EvergreenApi.__init__ = MagicMock()
        EvergreenApi.__init__.return_value = None
        EvergreenApi.get_api(auth=sample_evergreen_auth)
        EvergreenApi.__init__.assert_called_once_with(auth=sample_evergreen_auth,
                                                      timeout=DEFAULT_NETWORK_TIMEOUT_SEC)

    @patch(ns('read_evergreen_config'))
    def test_uses_default_config_file(self, mock_read_evergreen_config,
                                      sample_evergreen_configuration, sample_evergreen_auth):
        EvergreenApi.__init__ = MagicMock()
        EvergreenApi.__init__.return_value = None
        mock_read_evergreen_config.return_value = sample_evergreen_configuration
        EvergreenApi.get_api(use_config_file=True)
        EvergreenApi.__init__.assert_called_once_with(auth=sample_evergreen_auth,
                                                      timeout=DEFAULT_NETWORK_TIMEOUT_SEC)

    @patch(ns('read_evergreen_from_file'))
    def test_uses_passed_config_file(self, read_evergreen_from_file,
                                      sample_evergreen_configuration, sample_evergreen_auth):
        EvergreenApi.__init__ = MagicMock()
        EvergreenApi.__init__.return_value = None
        read_evergreen_from_file.return_value = sample_evergreen_configuration
        EvergreenApi.get_api(config_file='config.yml')
        EvergreenApi.__init__.assert_called_once_with(auth=sample_evergreen_auth,
                                                      timeout=DEFAULT_NETWORK_TIMEOUT_SEC)


class TestRaiseForStatus(object):
    @pytest.mark.skipif(
        sys.version_info.major == 2,
        reason='JSONDecodeError is not used in python2'
    )
    def test_non_json_error(self, mocked_api):
        mocked_response = MagicMock()
        mocked_response.json.side_effect = JSONDecodeError('json error', '', 0)
        mocked_response.status_code = 500
        mocked_response.raise_for_status.side_effect = HTTPError()
        mocked_api.session.get.return_value = mocked_response

        with pytest.raises(HTTPError):
            mocked_api.version_by_id('version_id')

        mocked_response.raise_for_status.assert_called_once()

    def test_json_errors_are_passed_through(self, mocked_api):
        error_msg = 'the error'
        mocked_response = MagicMock()
        mocked_response.json.return_value = {'error': error_msg}
        mocked_response.status_code = 500
        mocked_response.raise_for_status.side_effect = HTTPError()
        mocked_api.session.get.return_value = mocked_response

        with pytest.raises(HTTPError) as excinfo:
            mocked_api.version_by_id('version_id')

        assert error_msg in str(excinfo.value)
        mocked_response.raise_for_status.assert_not_called()


class TestLazyPagination(object):
    def test_with_no_next(self, mocked_api):
        returned_items = ['item 1', 'item 2', 'item 3']
        mocked_api.session.get.return_value.json.return_value = returned_items

        results = mocked_api._lazy_paginate('http://url')

        result_count = 0
        for result in results:
            assert result in returned_items
            result_count += 1

        assert len(returned_items) == result_count

    def test_next_in_response(self, mocked_api):
        returned_items = ['item 1', 'item 2', 'item 3']
        next_url = 'http://url_to_next'
        mocked_api.session.get.return_value.json.return_value = returned_items
        mocked_api.session.get.return_value.links = {
            'next': {
                'url': next_url
            }
        }

        results = mocked_api._lazy_paginate('http://url')

        items_to_check = len(returned_items) * 3
        for i, result in enumerate(results):
            assert result in returned_items
            if i > items_to_check:
                break

        assert i > items_to_check


class TestDistrosApi(object):
    def test_all_distros(self, mocked_api):
        mocked_api.all_distros()
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/distros'),
                                                  params=None, timeout=None)


class TestHostApi(object):
    def test_all_hosts(self, mocked_api):
        mocked_api.all_hosts()
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/hosts'), params={},
                                                  timeout=None)

    def test_all_hosts_with_status(self, mocked_api):
        mocked_api.all_hosts(status='success')
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/hosts'),
                                                  params={'status': 'success'}, timeout=None)


class TestProjectApi(object):
    def test_all_projects(self, mocked_api):
        mocked_api.all_projects()
        expected_url = mocked_api._create_url('/projects')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_project_by_id(self, mocked_api):
        mocked_api.project_by_id('project_id')
        expected_url = mocked_api._create_url('/projects/project_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_recent_version_by_project(self, mocked_api):
        mocked_api.recent_version_by_project('project_id')
        expected_url = mocked_api._create_url('/projects/project_id/recent_versions')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_version_by_project(self, mocked_api):
        returned_versions = mocked_api.versions_by_project('project_id')
        expected_url = mocked_api._create_url('/projects/project_id/versions')
        expected_params = {
            'requester': 'gitter_request'
        }
        next(returned_versions)
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_patches_by_project(self, mocked_api):
        patches = mocked_api.patches_by_project('project_id')
        next(patches)
        expected_url = mocked_api._create_url('/projects/project_id/patches')
        mocked_api.session.get.assert_called_with(url=expected_url, params={'limit': 100},
                                                  timeout=None)

    def test_commit_queue_for_project(self, mocked_api):
        mocked_api.commit_queue_for_project('project_id')
        expected_url = mocked_api._create_url('/commit_queue/project_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_test_stats_by_project(self, mocked_api):
        after_date = '2019-01-01'
        before_date = '2019-02-01'
        mocked_api.test_stats_by_project('project_id', after_date, before_date)
        expected_url = mocked_api._create_url('/projects/project_id/test_stats')
        expected_params = {
            'after_date': after_date,
            'before_date': before_date,
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_tasks_by_project(self, mocked_api):
        mocked_api.tasks_by_project('project_id')
        expected_url = mocked_api._create_url('/projects/project_id/versions/tasks')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_tasks_by_project_with_statuses(self, mocked_api):
        mocked_api.tasks_by_project('project_id', statuses=['status1'])
        expected_url = mocked_api._create_url('/projects/project_id/versions/tasks')
        mocked_api.session.get.assert_called_with(url=expected_url, params={'status': ['status1']},
                                                  timeout=None)


class TestBuildApi(object):
    def test_build_by_id(self, mocked_api):
        mocked_api.build_by_id('build_id')
        expected_url = mocked_api._create_url('/builds/build_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_tasks_by_build(self, mocked_api):
        mocked_api.tasks_by_build('build_id')
        expected_url = mocked_api._create_url('/builds/build_id/tasks')
        mocked_api.session.get.assert_called_with(url=expected_url, params={}, timeout=None)


class TestVersionApi(object):
    def test_version_by_id(self, mocked_api):
        mocked_api.version_by_id('version_id')
        expected_url = mocked_api._create_url('/versions/version_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_builds_by_version(self, mocked_api):
        mocked_api.builds_by_version('version_id')
        expected_url = mocked_api._create_url('/versions/version_id/builds')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)


class TestPatchApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.patch_by_id('patch_id')
        expected_url = mocked_api._create_url('/patches/patch_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)


class TestTaskApi(object):
    def test_task_by_id(self, mocked_api):
        mocked_api.task_by_id('task_id')
        expected_url = mocked_api._create_url('/tasks/task_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)

    def test_task_by_id_with_fetch_executions(self, mocked_api):
        mocked_api.task_by_id('task_id', fetch_all_executions=True)
        expected_url = mocked_api._create_url('/tasks/task_id')
        expected_params = {
            'fetch_all_executions': True
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_tests_by_task(self, mocked_api):
        mocked_api.tests_by_task('task_id')
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {}
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_tests_by_task_with_status(self, mocked_api):
        mocked_api.tests_by_task('task_id', status='success')
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'status': 'success'
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_tests_by_task_with_execution(self, mocked_api):
        mocked_api.tests_by_task('task_id', execution=5)
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'execution': 5
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_tests_by_task_with_status_and_execution(self, mocked_api):
        mocked_api.tests_by_task('task_id', status='success', execution=5)
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'status': 'success',
            'execution': 5
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_performance_results_by_task(self, mocked_api):
        mocked_api.performance_results_by_task('task_id')
        expected_url = mocked_api._create_plugin_url('/task/task_id/perf')
        expected_params = None
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)

    def test_performance_results_by_task_name(self, mocked_api):
        mocked_api.performance_results_by_task_name('task_id', 'task_name')
        expected_url = '{api_server}/api/2/task/task_id/json/history/task_name/perf'.format(
            api_server=DEFAULT_API_SERVER)
        expected_params = None
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params,
                                                  timeout=None)


class TestOldApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.manifest('project_id', 'revision')
        expected_url = mocked_api._create_old_url('plugin/manifest/get/project_id/revision')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None, timeout=None)


class TestLogApi(object):
    def test_retrieve_log(self, mocked_api):
        mocked_api.retrieve_task_log('log_url')
        mocked_api.session.get.assert_called_with(url='log_url', params={}, timeout=None)

    def test_retrieve_log_with_raw(self, mocked_api):
        mocked_api.retrieve_task_log('log_url', raw=True)
        mocked_api.session.get.assert_called_with(url='log_url', params={'text': 'true'},
                                                  timeout=None)


class TestCachedEvergreenApi(object):
    def test_build_by_id_is_cached(self, mocked_cached_api):
        build_id = 'some build id'
        another_build_id = 'some other build id'
        mocked_cached_api.build_by_id(build_id)
        mocked_cached_api.build_by_id(build_id)
        mocked_cached_api.build_by_id(another_build_id)
        assert mocked_cached_api.session.get.call_count == 2

    def test_version_by_id_is_cached(self, mocked_cached_api):
        version_id = 'some version id'
        another_version_id = 'some other version id'
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.version_by_id(another_version_id)
        assert mocked_cached_api.session.get.call_count == 2

    def test_clear_caches(self, mocked_cached_api):
        build_id = 'some build id'
        version_id = 'some version id'
        assert mocked_cached_api.build_by_id(build_id)
        assert mocked_cached_api.version_by_id(version_id)
        mocked_cached_api.clear_caches()
        assert mocked_cached_api.build_by_id(build_id)
        assert mocked_cached_api.version_by_id(version_id)
        assert mocked_cached_api.session.get.call_count == 4


class TestRetryingEvergreenApi(object):
    def test_no_retries_on_success(self, mocked_retrying_api):
        version_id = 'version id'

        mocked_retrying_api.version_by_id(version_id)
        assert mocked_retrying_api.session.get.call_count == 1

    @pytest.mark.skipif(
        not os.environ.get('RUN_SLOW_TESTS'),
        reason='Slow running test due to retries'
    )
    def test_three_retries_on_failure(self, mocked_retrying_api):
        version_id = 'version id'
        mocked_retrying_api.session.get.side_effect = HTTPError()

        with pytest.raises(RetryError):
            mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.get.call_count == under_test.MAX_RETRIES

    @pytest.mark.skipif(
        not os.environ.get('RUN_SLOW_TESTS'),
        reason='Slow running test due to retries'
    )
    def test_pass_on_retries_after_failure(self, mocked_retrying_api):
        version_id = 'version id'
        successful_response = mocked_retrying_api.session.get.return_value
        mocked_retrying_api.session.get.side_effect = [HTTPError(), successful_response]

        mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.get.call_count == 2

    def test_no_retries_on_non_http_errors(self, mocked_retrying_api):
        version_id = 'version id'
        mocked_retrying_api.session.get.side_effect = ValueError('Unexpected Failure')

        with pytest.raises(ValueError):
            mocked_retrying_api.version_by_id(version_id)

        assert mocked_retrying_api.session.get.call_count == 1
