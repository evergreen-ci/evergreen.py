# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from collections import namedtuple
import logging
import os
import time

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # type: ignore

import requests
import yaml

from evergreen.task import Task
from evergreen.build import Build


EvgAuth = namedtuple('EvgAuth', ['username', 'api_key'])

LOGGER = logging.getLogger(__name__)
DEFAULT_API_SERVER = 'http://evergreen.mongodb.com'
CONFIG_FILE_LOCATIONS = [
    os.path.join('.', '.evergreen.yml'),
    os.path.expanduser(os.path.join('~', '.evergreen.yml')),
    os.path.expanduser(os.path.join('~', 'cli_bin', '.evergreen.yml')),
]


def read_evergreen_config():
    """
    Search known location for the evergreen config file.

    :return: First found evergreen configuration.
    """
    for filename in [filename for filename in CONFIG_FILE_LOCATIONS if os.path.isfile(filename)]:
        with open(filename, 'r') as fstream:
            return yaml.safe_load(fstream)

    return None


class EvergreenApi(object):
    """Access to the Evergreen API Server."""

    def __init__(self, api_server=DEFAULT_API_SERVER, auth=None):
        """Create an Evergreen Api object."""
        self._api_server = api_server
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter()
        self.session.mount('{url.scheme}://'.format(url=urlparse(api_server)), adapter)
        if auth:
            self.session.headers.update({
                'Api-User': auth.username,
                'Api-Key': auth.api_key,
            })

    @classmethod
    def get_api(cls):
        """
        Get an evergreen api instance based on config file settings.

        :return: EvergreenApi instance.
        """
        config = read_evergreen_config()

        return cls(auth=EvgAuth(config['user'], config['api_key']))

    def tasks_by_build_id(self, build_id, params=None):
        """
        Get all tasks for a given build_id.

        :param build_id: build_id to query.
        :param params: Dictionary of parameters to pass to query.
        :return: List of tasks for the specified build.
        """
        url = '{api_server}/rest/v2/builds/{build_id}/tasks'.format(api_server=self._api_server,
                                                                    build_id=build_id)
        return [Task(task) for task in self._paginate(url, params)]

    def builds_by_version(self, version_id, params=None):
        """
        Get all builds for a given Evergreen version_id.

        :param version_id: Version Id to query for.
        :param params: Dictionary of parameters to pass to query.
        :return: List of builds for the specified version.
        """
        url = '{api_server}/rest/v2/version/{version_id}/builds'.format(api_server=self._api_server,
                                                                        version_id=version_id)
        return [Build(build) for build in self._paginate(url, params)]

    @staticmethod
    def _log_api_call_time(response, start_time):
        duration = round(time.time() - start_time, 2)
        if duration > 10:
            LOGGER.info('Request %s took %fs', response.request.url, duration)
        else:
            LOGGER.debug('Request %s took %fs', response.request.url, duration)

    def _call_api(self, url, params=None):
        start_time = time.time()
        response = self.session.get(url=url, params=params)
        self._log_api_call_time(response, start_time)

        response.raise_for_status()
        return response

    def _paginate(self, url, params=None):
        """Paginate until all results are returned and return a list of all JSON results."""
        response = self._call_api(url, params)
        json_data = response.json()
        while "next" in response.links:
            response = self._call_api(response.links['next']['url'])
            if response.json():
                json_data.extend(response.json())

        return json_data
