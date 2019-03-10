# -*- encoding: utf-8 -*-
"""Get configuration about connecting to evergreen."""
from __future__ import absolute_import

from collections import namedtuple
import os

import yaml

EvgAuth = namedtuple('EvgAuth', ['username', 'api_key'])

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


def get_auth_from_config(config):
    """
    Get the evergreen authentication from the specified config file.

    :param config: Evergreen configuration.
    :return: Authentication information for evergreen.
    """
    return EvgAuth(config['user'], config['api_key'])
