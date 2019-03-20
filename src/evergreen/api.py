# -*- encoding: utf-8 -*-
"""API for interacting with evergreen."""
from __future__ import absolute_import

import logging
import time

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # type: ignore

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

import requests

from evergreen.build import Build
from evergreen.config import read_evergreen_config, DEFAULT_API_SERVER, get_auth_from_config
from evergreen.host import Host
from evergreen.manifest import Manifest
from evergreen.patch import Patch
from evergreen.project import Project
from evergreen.task import Task
from evergreen.stats import TestStats
from evergreen.util import evergreen_input_to_output
from evergreen.version import Version

LOGGER = logging.getLogger(__name__)
CACHE_SIZE = 5000
DEFAULT_LIMIT = 100


class _BaseEvergreenApi(object):
    """Base methods for building API objects."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """
        Create a _BaseEvergreenApi object.

        :param api_server: URI of Evergreen API server.
        :param auth: EvgAuth object with auth information.
        """
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
            LOGGER.info('Request %s took %fs', response.request.url, duration)
        else:
            LOGGER.debug('Request %s took %fs', response.request.url, duration)

    def _call_api(self, url, params=None):
        """
        Make a call to the evergreen api.

        :param url: Url of call to make.
        :param params: parameters to pass to api.
        :return: response from api server.
        """
        start_time = time.time()
        response = self.session.get(url=url, params=params)
        self._log_api_call_time(response, start_time)

        self._raise_for_status(response)
        return response

    @staticmethod
    def _raise_for_status(response):
        """
        Raise an exception with the evergreen message if it exists.

        :param response: response from evergreen api.
        """
        if response.status_code >= 400 and 'error' in response.json():
            raise requests.exceptions.HTTPError(response.json()['error'], response=response)

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


class _HostApi(_BaseEvergreenApi):
    """API for hosts endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_HostApi, self).__init__(api_server, auth)

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

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_ProjectApi, self).__init__(api_server, auth)

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

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_BuildApi, self).__init__(api_server, auth)

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

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_VersionApi, self).__init__(api_server, auth)

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

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_PatchApi, self).__init__(api_server, auth)

    def patch_by_id(self, patch_id, params=None):
        """
        Get a patch by patch id.

        :param patch_id: Id of patch to query for.
        :param params: Parameters to pass to endpoint.
        :return: Patch queried for.
        """
        url = self._create_url('/patches/{patch_id}'.format(patch_id=patch_id))
        return Patch(self._call_api(url, params).json(), self)


class _OldApi(_BaseEvergreenApi):
    """API for pre-v2 endpoints."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(_OldApi, self).__init__(api_server, auth)

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


class EvergreenApi(_ProjectApi, _BuildApi, _VersionApi, _PatchApi, _HostApi, _OldApi):
    """Access to the Evergreen API Server."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(EvergreenApi, self).__init__(api_server, auth)

    @classmethod
    def get_api(cls, auth=None, use_config_file=False):
        """
        Get an evergreen api instance based on config file settings.

        :param auth: EvgAuth with authentication to use.
        :param use_config_file: attempt to read auth from config file.
        :return: EvergreenApi instance.
        """
        if not auth and use_config_file:
            config = read_evergreen_config()
            auth = get_auth_from_config(config)

        return cls(auth=auth)


class CachedEvergreenApi(EvergreenApi):
    """
    Access to the Evergreen API server that caches certain calls.
    """

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        super(CachedEvergreenApi, self).__init__(api_server, auth)

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
