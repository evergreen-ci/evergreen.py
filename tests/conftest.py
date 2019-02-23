import json
import os

import pytest


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
