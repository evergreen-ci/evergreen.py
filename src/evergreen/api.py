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

    def tasks_by_build_id(self, build_id):
        """
        Get all tasks for a given build_id.

        :param build_id: build_id to query.
        :return: List of tasks for the specified build.
        """
        url = '{api_server}/rest/v2/builds/{build_id}/tasks'.format(api_server=self._api_server,
                                                                    build_id=build_id)
        return self._call_api(url).json()

    def _call_api(self, url, params=None):
        start_time = time.time()
        response = self.session.get(url=url, params=params)
        duration = round(time.time() - start_time, 2)
        if duration > 10:
            LOGGER.info('Request %s took %fs', response.request.url, duration)
        else:
            LOGGER.debug('Request %s took %fs', response.request.url, duration)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            LOGGER.error('Response text: %s', response.text)
            raise err
        return response
