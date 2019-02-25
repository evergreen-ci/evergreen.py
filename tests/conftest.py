import json
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
import os

import pytest

from evergreen.api import EvergreenApi


SAMPLE_DATA_PATH = os.path.join('tests', 'evergreen', 'data')


def get_sample_json(file):
    """Read json data from the specified sample file."""
    with open(os.path.join(SAMPLE_DATA_PATH, file), 'r') as file_data:
        return json.load(file_data)


@pytest.fixture()
def sample_host():
    """Return sample host json."""
    return get_sample_json('host.json')


@pytest.fixture()
def sample_task():
    """Return sample task json."""
    return get_sample_json('task.json')


@pytest.fixture()
def sample_version():
    """Return sample version json."""
    return get_sample_json('version.json')


@pytest.fixture()
def sample_test_stats():
    """Return sample test_stats json."""
    return get_sample_json('test_stats.json')


@pytest.fixture()
def mocked_api():
    """Return an Evergreen API with a mocked session."""
    api = EvergreenApi()
    api.session = MagicMock()
    response_mock = MagicMock()
    response_mock.status_code = 200
    api.session.get.return_value = response_mock
    return api
