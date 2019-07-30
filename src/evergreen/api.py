# -*- encoding: utf-8 -*-
"""API for interacting with evergreen."""
from __future__ import absolute_import

import time

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError  # JSONDecodeError doesn't exist in python 2, ValueError is used.

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # type: ignore

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

import requests
import structlog
from structlog.stdlib import LoggerFactory
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from evergreen.build import Build
from evergreen.commitqueue import CommitQueue
from evergreen.config import read_evergreen_config, DEFAULT_API_SERVER, get_auth_from_config,\
    read_evergreen_from_file, DEFAULT_NETWORK_TIMEOUT_SEC
from evergreen.distro import Distro
from evergreen.host import Host
from evergreen.manifest import Manifest
from evergreen.patch import Patch
from evergreen.project import Project
from evergreen.task import Task
from evergreen.tst import Tst
from evergreen.stats import TestStats
from evergreen.util import evergreen_input_to_output
from evergreen.version import Version

structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.getLogger(__name__)

CACHE_SIZE = 5000
DEFAULT_LIMIT = 100
MAX_RETRIES = 3
START_WAIT_TIME_SEC = 2
MAX_WAIT_TIME_SEC = 5


class _BaseEvergreenApi(object):
    """Base methods for building API objects."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """
        Create a _BaseEvergreenApi object.

        :param api_server: URI of Evergreen API server.
        :param auth: EvgAuth object with auth information.
        """
        self._timeout = timeout
        self._api_server = api_server
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter()
        self.session.mount('{url.scheme}://'.format(url=urlparse(api_server)), adapter)
        if auth:
            self.session.headers.update({
                'Api-User': auth.username,
                'Api-Key': auth.api_key,
            })

    def _create_url(self, endpoint):
        """
        Format the a call to an endpoint.

        :param endpoint: endpoint to call.
        :return: Full url to get endpoint.
        """
        return '{api_server}/rest/v2{endpoint}'.format(
            api_server=self._api_server, endpoint=endpoint)

    @staticmethod
    def _log_api_call_time(response, start_time):
        """
        Log how long the api call took.

        :param response: Response from API.
        :param start_time: Time the response was started.
        """
        duration = round(time.time() - start_time, 2)
        if duration > 10:
            LOGGER.info('Request completed.', url=response.request.url, duration=duration)
        else:
            LOGGER.debug('Request completed.', url=response.request.url, duration=duration)

    def _call_api(self, url, params=None):
        """
        Make a call to the evergreen api.

        :param url: Url of call to make.
        :param params: parameters to pass to api.
        :return: response from api server.
        """
        start_time = time.time()
        response = self.session.get(url=url, params=params, timeout=self._timeout)
        self._log_api_call_time(response, start_time)

        self._raise_for_status(response)
        return response

    @staticmethod
    def _raise_for_status(response):
        """
        Raise an exception with the evergreen message if it exists.

        :param response: response from evergreen api.
        """
        try:
            json_data = response.json()
            if response.status_code >= 400 and 'error' in json_data:
                raise requests.exceptions.HTTPError(json_data['error'], response=response)
        except JSONDecodeError:
            pass

        response.raise_for_status()

    def _paginate(self, url, params=None):
        """
        Paginate until all results are returned and return a list of all JSON results.

        :param url: url to make request to.
        :param params: parameters to pass to request.
        :return: json list of all results.
        """
        response = self._call_api(url, params)
        json_data = response.json()
        while "next" in response.links:
            if params and 'limit' in params and len(json_data) >= params['limit']:
                break
            response = self._call_api(response.links['next']['url'])
            if response.json():
                json_data.extend(response.json())

        return json_data

    def _lazy_paginate_by_date(self, url, params=None):
        """
        Paginate based on date, the results are returned lazily.

        :param url: URL to query.
        :param params: Params to pass to url.
        :return: A generator to get results from.
        """
        if not params:
            params = {
                'limit': DEFAULT_LIMIT,
            }

        while True:
            data = self._call_api(url, params).json()
            if not data:
                break
            for result in data:
                yield result
            params['start_at'] = evergreen_input_to_output(data[-1]['create_time'])


class _DistrosApi(_BaseEvergreenApi):
    """API for distros endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_DistrosApi, self).__init__(api_server, auth, timeout)

    def all_distros(self):
        """
        Get all distros in evergreen.

        :return: List of all distros in evergreen.
        """
        url = self._create_url('/distros')
        distro_list = self._paginate(url)
        return [Distro(distro, self) for distro in distro_list]


class _HostApi(_BaseEvergreenApi):
    """API for hosts endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_HostApi, self).__init__(api_server, auth, timeout)

    def all_hosts(self, status=None):
        """
        Get all hosts in evergreen.

        :param status: Only return hosts with specified status.
        :return: List of all hosts in evergreen.
        """
        params = {}
        if status:
            params['status'] = status

        url = self._create_url('/hosts')
        host_list = self._paginate(url, params)
        return [Host(host, self) for host in host_list]


class _ProjectApi(_BaseEvergreenApi):
    """API for project endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_ProjectApi, self).__init__(api_server, auth, timeout)

    def all_projects(self):
        """
        Get all projects in evergreen.

        :return: List of all projects in evergreen.
        """
        url = self._create_url('/projects')
        project_list = self._paginate(url)
        return [Project(project, self) for project in project_list]

    def project_by_id(self, project_id):
        """
        Get a project by project_id.

        :param project_id: Id of project to query.
        :return: Project specified.
        """
        url = self._create_url('/projects/{project_id}'.format(project_id=project_id))
        return Project(self._paginate(url), self)

    def recent_version_by_project(self, project_id, params=None):
        """
        Get recent versions created in specified project.

        :param project_id: Id of project to query.
        :param params: parameters to pass to endpoint.
        :return: List of recent versions.
        """
        url = self._create_url(
            '/projects/{project_id}/recent_versions'.format(project_id=project_id))
        version_list = self._paginate(url, params)
        return [Version(version, self) for version in version_list]

    def patches_by_project(self, project_id, params=None):
        """
        Get a list of patches for the specified project.

        :param project_id: Id of project to query.
        :param params: parameters to pass to endpoint.
        :return: List of recent patches.
        """
        url = self._create_url('/projects/{project_id}/patches'.format(project_id=project_id))
        patches = self._lazy_paginate_by_date(url, params)
        return (Patch(patch, self) for patch in patches)

    def commit_queue_for_project(self, project_id):
        """
        Get the current commit queue for the specified project.

        :param project_id: Id of project to query.
        :return: Current commit queue for project.
        """
        url = self._create_url('/commit_queue/{project_id}'.format(project_id=project_id))
        return CommitQueue(self._paginate(url), self)

    def test_stats_by_project(self,
                              project_id,
                              after_date,
                              before_date,
                              group_num_days=None,
                              requesters=None,
                              tests=None,
                              tasks=None,
                              variants=None,
                              distros=None,
                              group_by=None,
                              sort=None):
        """
        Get a patch by patch id.

        :param project_id: Id of patch to query for.
        :param after_date: Collect stats after this date.
        :param before_date: Collect stats before this date.
        :param group_num_days: Aggregate statistics to this size.
        :param requesters: Filter by requestors (mainline, patch, trigger, or adhoc).
        :param tests: Only include specified tests.
        :param tasks: Only include specified tasks.
        :param variants: Only include specified variants.
        :param distros: Only include specified distros.
        :param group_by: How to group results (test_task_variant, test_task, or test)
        :param sort: How to sort results (earliest or latest).
        :return: Patch queried for.
        """
        params = {
            'after_date': after_date,
            'before_date': before_date,
        }
        if group_num_days:
            params['group_num_days'] = group_num_days
        if requesters:
            params['requesters'] = requesters
        if tests:
            params['tests'] = tests
        if tasks:
            params['tasks'] = tasks
        if variants:
            params['variants'] = variants
        if distros:
            params['distros'] = distros
        if group_by:
            params['group_by'] = group_by
        if sort:
            params['sort'] = sort
        url = self._create_url('/projects/{project_id}/test_stats'.format(project_id=project_id))
        test_stats_list = self._paginate(url, params)
        return [TestStats(test_stat, self) for test_stat in test_stats_list]


class _BuildApi(_BaseEvergreenApi):
    """API for build endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_BuildApi, self).__init__(api_server, auth, timeout)

    def build_by_id(self, build_id):
        """
        Get a build by id.

        :param build_id: build id to query.
        :return: Build queried for.
        """
        url = self._create_url('/builds/{build_id}'.format(build_id=build_id))
        return Build(self._paginate(url), self)

    def tasks_by_build(self, build_id, fetch_all_executions=None):
        """
        Get all tasks for a given build.

        :param build_id: build_id to query.
        :param fetch_all_executions: Fetch all executions for a given task.
        :return: List of tasks for the specified build.
        """
        params = {}
        if fetch_all_executions:
            params['fetch_all_executions'] = 1

        url = self._create_url('/builds/{build_id}/tasks'.format(build_id=build_id))
        task_list = self._paginate(url, params)
        return [Task(task, self) for task in task_list]


class _VersionApi(_BaseEvergreenApi):
    """API for version endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_VersionApi, self).__init__(api_server, auth, timeout)

    def version_by_id(self, version_id):
        """
        Get version by version id.

        :param version_id: Id of version to query.
        :return: Version queried for.
        """
        url = self._create_url('/versions/{version_id}'.format(version_id=version_id))
        return Version(self._paginate(url), self)

    def builds_by_version(self, version_id, params=None):
        """
        Get all builds for a given Evergreen version_id.

        :param version_id: Version Id to query for.
        :param params: Dictionary of parameters to pass to query.
        :return: List of builds for the specified version.
        """
        url = self._create_url('/versions/{version_id}/builds'.format(version_id=version_id))
        build_list = self._paginate(url, params)
        return [Build(build, self) for build in build_list]


class _PatchApi(_BaseEvergreenApi):
    """API for patch endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_PatchApi, self).__init__(api_server, auth, timeout)

    def patch_by_id(self, patch_id, params=None):
        """
        Get a patch by patch id.

        :param patch_id: Id of patch to query for.
        :param params: Parameters to pass to endpoint.
        :return: Patch queried for.
        """
        url = self._create_url('/patches/{patch_id}'.format(patch_id=patch_id))
        return Patch(self._call_api(url, params).json(), self)


class _TaskApi(_BaseEvergreenApi):
    """API for task endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_TaskApi, self).__init__(api_server, auth, timeout)

    def task_by_id(self, task_id, fetch_all_executions=None):
        """
        Get a task by task_id.

        :param task_id: Id of task to query for.
        :param fetch_all_executions: Should all executions of the task be fetched.
        :return: Task queried for.
        """
        params = None
        if fetch_all_executions:
            params = {'fetch_all_executions': fetch_all_executions}
        url = self._create_url('/tasks/{task_id}'.format(task_id=task_id))
        return Task(self._call_api(url, params).json(), self)

    def tests_by_task(self, task_id, status=None, execution=None):
        """
        Get all tests for a given task.

        :param task_id: Id of task to query for.
        :param status: Limit results to given status.
        :param execution: Retrieve the specified task execution (defaults to 0).
        :return: List of tests for the specified task.
        """
        params = {}
        if status:
            params['status'] = status
        if execution:
            params['execution'] = execution
        url = self._create_url('/tasks/{task_id}/tests'.format(task_id=task_id))
        return [Tst(test, self) for test in self._paginate(url, params)]


class _OldApi(_BaseEvergreenApi):
    """API for pre-v2 endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_OldApi, self).__init__(api_server, auth, timeout)

    def _create_old_url(self, endpoint):
        """
        Build a url for an pre-v2 endpoint.

        :param endpoint: endpoint to build url for.
        :return: An string pointing to the given endpoint.
        """
        return '{api_server}/{endpoint}'.format(api_server=self._api_server, endpoint=endpoint)

    def manifest(self, project_id, revision):
        """
        Get the manifest for the given revision.

        :param project_id: Project the revision belongs to.
        :param revision: Revision to get manifest of.
        :return: Manifest of the given revision of the given project.
        """
        url = self._create_old_url('plugin/manifest/get/{project_id}/{revision}'.format(
            project_id=project_id, revision=revision))
        return Manifest(self._call_api(url).json(), self)


class _LogApi(_BaseEvergreenApi):
    """API for accessing log files."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(_LogApi, self).__init__(api_server, auth, timeout)

    def retrieve_task_log(self, log_url, raw=False):
        """
        Get the request log file from a task.

        :param log_url: URL of log to retrieve.
        :param raw: Retrieve the raw version of the log
        :return: Contents of specified log file.
        """
        params = {}
        if raw:
            params['text'] = 'true'
        return self._call_api(log_url, params=params).text


class EvergreenApi(_ProjectApi, _BuildApi, _VersionApi, _PatchApi, _HostApi, _TaskApi, _OldApi,
                   _LogApi, _DistrosApi):
    """Access to the Evergreen API Server."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(EvergreenApi, self).__init__(api_server, auth, timeout=timeout)

    @classmethod
    def get_api(cls, auth=None, use_config_file=False, config_file=None,
                timeout=DEFAULT_NETWORK_TIMEOUT_SEC):
        """
        Get an evergreen api instance based on config file settings.

        :param auth: EvgAuth with authentication to use.
        :param use_config_file: attempt to read auth from default config file.
        :param config_file: config file with authentication information.
        :param timeout: Network timeout.
        :return: EvergreenApi instance.
        """
        if not auth and use_config_file:
            config = read_evergreen_config()
            auth = get_auth_from_config(config)

        if not auth and config_file:
            config = read_evergreen_from_file(config_file)
            auth = get_auth_from_config(config)

        return cls(auth=auth, timeout=timeout)


class CachedEvergreenApi(EvergreenApi):
    """
    Access to the Evergreen API server that caches certain calls.
    """

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(CachedEvergreenApi, self).__init__(api_server, auth, timeout)

    @lru_cache(maxsize=CACHE_SIZE)
    def build_by_id(self, build_id):
        """
        Get a build by id.

        :param build_id: build id to query.
        :return: Build queried for.
        """
        return super(CachedEvergreenApi, self).build_by_id(build_id)

    @lru_cache(maxsize=CACHE_SIZE)
    def version_by_id(self, version_id):
        """
        Get version by version id.

        :param version_id: Id of version to query.
        :return: Version queried for.
        """
        return super(CachedEvergreenApi, self).version_by_id(version_id)

    def clear_caches(self):
        """
        Clear the cache.
        """
        cached_functions = [
            self.build_by_id,
            self.version_by_id,
        ]
        for fn in cached_functions:
            fn.cache_clear()


class RetryingEvergreenApi(EvergreenApi):
    """An Evergreen Api that retries failed calls."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None, timeout=None):
        """Create an Evergreen Api object."""
        super(RetryingEvergreenApi, self).__init__(api_server, auth, timeout)

    @retry(retry=retry_if_exception_type(requests.exceptions.HTTPError),
           stop=stop_after_attempt(MAX_RETRIES),
           wait=wait_exponential(multiplier=1, min=START_WAIT_TIME_SEC, max=MAX_WAIT_TIME_SEC))
    def _call_api(self, url, params=None):
        """
        Call into the evergreen api.

        :param url: Url to call.
        :param params: Parameters to pass to api.
        :return: Result from calling API.
        """
        return super(RetryingEvergreenApi, self)._call_api(url, params)
