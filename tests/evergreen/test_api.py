
class TestDistrosApi(object):
    def test_all_distros(self, mocked_api):
        mocked_api.all_distros()
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/distros'),
                                                  params=None)


class TestHostApi(object):
    def test_all_hosts(self, mocked_api):
        mocked_api.all_hosts()
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/hosts'), params={})

    def test_all_hosts_with_status(self, mocked_api):
        mocked_api.all_hosts(status='success')
        mocked_api.session.get.assert_called_with(url=mocked_api._create_url('/hosts'),
                                                  params={'status': 'success'})


class TestProjectApi(object):
    def test_all_projects(self, mocked_api):
        mocked_api.all_projects()
        expected_url = mocked_api._create_url('/projects')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_project_by_id(self, mocked_api):
        mocked_api.project_by_id('project_id')
        expected_url = mocked_api._create_url('/projects/project_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_recent_version_by_project(self, mocked_api):
        mocked_api.recent_version_by_project('project_id')
        expected_url = mocked_api._create_url('/projects/project_id/recent_versions')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_patches_by_project(self, mocked_api):
        patches = mocked_api.patches_by_project('project_id')
        next(patches)
        expected_url = mocked_api._create_url('/projects/project_id/patches')
        mocked_api.session.get.assert_called_with(url=expected_url, params={'limit': 100})

    def test_commit_queue_for_project(self, mocked_api):
        mocked_api.commit_queue_for_project('project_id')
        expected_url = mocked_api._create_url('/projects/project_id/commit_queue')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_test_stats_by_project(self, mocked_api):
        after_date = '2019-01-01'
        before_date = '2019-02-01'
        mocked_api.test_stats_by_project('project_id', after_date, before_date)
        expected_url = mocked_api._create_url('/projects/project_id/test_stats')
        expected_params = {
            'after_date': after_date,
            'before_date': before_date,
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)


class TestBuildApi(object):
    def test_build_by_id(self, mocked_api):
        mocked_api.build_by_id('build_id')
        expected_url = mocked_api._create_url('/builds/build_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_tasks_by_build(self, mocked_api):
        mocked_api.tasks_by_build('build_id')
        expected_url = mocked_api._create_url('/builds/build_id/tasks')
        mocked_api.session.get.assert_called_with(url=expected_url, params={})


class TestVersionApi(object):
    def test_version_by_id(self, mocked_api):
        mocked_api.version_by_id('version_id')
        expected_url = mocked_api._create_url('/versions/version_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_builds_by_version(self, mocked_api):
        mocked_api.builds_by_version('version_id')
        expected_url = mocked_api._create_url('/versions/version_id/builds')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)


class TestPatchApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.patch_by_id('patch_id')
        expected_url = mocked_api._create_url('/patches/patch_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)


class TestTaskApi(object):
    def test_task_by_id(self, mocked_api):
        mocked_api.task_by_id('task_id')
        expected_url = mocked_api._create_url('/tasks/task_id')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)

    def test_task_by_id_with_fetch_executions(self, mocked_api):
        mocked_api.task_by_id('task_id', fetch_all_executions=True)
        expected_url = mocked_api._create_url('/tasks/task_id')
        expected_params = {
            'fetch_all_executions': True
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)

    def test_tests_by_task(self, mocked_api):
        mocked_api.tests_by_task('task_id')
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {}
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)

    def test_tests_by_task_with_status(self, mocked_api):
        mocked_api.tests_by_task('task_id', status='success')
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'status': 'success'
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)

    def test_tests_by_task_with_execution(self, mocked_api):
        mocked_api.tests_by_task('task_id', execution=5)
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'execution': 5
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)

    def test_tests_by_task_with_status_and_execution(self, mocked_api):
        mocked_api.tests_by_task('task_id', status='success', execution=5)
        expected_url = mocked_api._create_url('/tasks/task_id/tests')
        expected_params = {
            'status': 'success',
            'execution': 5
        }
        mocked_api.session.get.assert_called_with(url=expected_url, params=expected_params)


class TestOldApi(object):
    def test_patch_by_id(self, mocked_api):
        mocked_api.manifest('project_id', 'revision')
        expected_url = mocked_api._create_old_url('plugin/manifest/get/project_id/revision')
        mocked_api.session.get.assert_called_with(url=expected_url, params=None)


class TestLogApi(object):
    def test_retrieve_log(self, mocked_api):
        mocked_api.retrieve_task_log('log_url')
        mocked_api.session.get.assert_called_with(url='log_url', params={})

    def test_retrieve_log_with_raw(self, mocked_api):
        mocked_api.retrieve_task_log('log_url', raw=True)
        mocked_api.session.get.assert_called_with(url='log_url', params={'text': 'true'})


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
