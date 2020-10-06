# Evergreen.py

A client library for the Evergreen API written in python. Currently supports the V2 version of
the API. For more details, see https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage .

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/evergreen.py) ![PyPI](https://img.shields.io/pypi/v/evergreen.py.svg) [![Coverage Status](https://coveralls.io/repos/github/evergreen-ci/evergreen.py/badge.svg?branch=master)](https://coveralls.io/github/evergreen-ci/evergreen.py?branch=master)

## Documentation

You can find the documentation [here](https://evergreen-ci.github.io/evergreen.py/).

## Usage

```
>>> from evergreen.api import EvgAuth, EvergreenApi
>>> api = EvergreenApi.get_api(EvgAuth('david.bradford', '***'))
>>> project = api.project_by_id('mongodb-mongo-master')
>>> project.display_name
'MongoDB (master)'
```

### Command Line Application

A command line application is included to explore the evergreen api data. It is called `evg-api`.

```
$ evg-api --json list-hosts
{
    "host_id": "host num 0",
    "host_url": "host.num.com",
    "distro": {
        "distro_id": "ubuntu1804-build",
        "provider": "static",
        "image_id": ""
    },
    "provisioned": true,
    "started_by": "mci",
    "host_type": "",
    "user": "mci-exec",
    "status": "running",
    "running_task": {
        "task_id": null,
        "name": null,
        "dispatch_time": null,
        "version_id": null,
        "build_id": null
    },
    "user_host": false
}
...
```

It may also be used from inside the repo using
```
$ poetry install
$ poetry run python src/evergreen/cli/main.py
```

## Contributors Guide

### Testing

Use poetry and pytest for testing.
```
$ poetry install
$ poetry run pytest
```

To get code coverage information:

```
$ poetry run pytest --cov=src --cov-report=html
```

This will generate an html coverage report in `htmlcov/` directory.

There are a few tests that are slow running. These tests are not run by default, but can be included
by setting the env variable RUN_SLOW_TESTS to any value.

```
$ RUN_SLOW_TEST=1 poetry run pytest
```
### Running checks on commit

This project has [pre-commit](https://pre-commit.com/) configured. Pre-commit will run configured
checks at git commit time. To enable pre-commit on your local repository run:

```bash
$ poetry run pre-commit install
```

### Versioning and Deploy

Before deploying a new version, please update the `CHANGELOG.md` file with a description of what
is being changed.

Deploys to [PyPi](https://pypi.org/project/evergreen.py/) are done automatically on merges to master.
In order to avoid overwriting a previous deploy, the version should be updated on all changes. The
[semver](https://semver.org/) versioning scheme should be used for determining the version number.

The version is found in the `pyproject.toml` file.

### Merging

Merges to master should be done by the evergreen [commit queue](https://github.com/evergreen-ci/evergreen/wiki/Commit-Queue#pr).
After a PR has been reviewed, add a comment with the text `evergreen merge` to merge the PR.
