# Evergreen.py

A client library for the Evergreen API written in python. Currently supports the V2 version of
the API. For more details, see https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/evergreen.py) [![PyPI](https://img.shields.io/pypi/v/evergreen.py.svg)](https://pypi.org/project/evergreen.py/) [![Coverage Status](https://coveralls.io/repos/github/evergreen-ci/evergreen.py/badge.svg?branch=master)](https://coveralls.io/github/evergreen-ci/evergreen.py?branch=master)

## Table of contents

1. [Description](#description)
2. [Getting Help](#getting-help)
3. [Dependencies](#dependencies)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Documentation](#documentation)
7. [Contributor's Guide](#contributors-guide)
   - [Setting up a local development environment](#setting-up-a-local-development-environment)
   - [Linting/formatting](#lintingformatting)
   - [Running tests](#running-tests)
   - [Automatically running checks on commit](#automatically-running-checks-on-commit)
   - [Versioning](#versioning)
   - [Code Review](#code-review)
   - [Deployment](#deployment)

## Description

This is a Python client library for interacting with Evergreen and Evergreen objects. It currently only
supports the V2 version of Evergreen's api. It can be used either by Python code in a separate application
or on the command line to get data about Evergreen objects quickly and easily.

## Getting Help

### What's the right channel to ask my question?

If you have a question about evergreen.py, please mention @dag-on-call in
slack channel [#evergreen-users](https://mongodb.slack.com/messages/#evergreen-users/),
or email us at devprod-si-team@mongodb.com.

### How can I request a change/report a bug in evergreen.py?

Create a [DEVPROD ticket](https://jira.mongodb.org/projects/DEVPROD).

### What should I include in my ticket or #evergreen-users question?

Since #evergreen-users questions are interrupts,
please include as much information as possible.
This can help avoid long information-gathering threads.

Please include the following:

- **Motivation for Request**
  - provide us the motivation for this change.
- **Context**
  - provide some background contexts for this issue.
- **Description**
  - provide some descriptions on how this issue happened.

## Dependencies

- Python 3.9 or later

## Installation

```bash
$ pip install evergreen.py
```

## Usage

This client can be used either in code or directly via the command line.

In code:

```python
>> from evergreen.api import EvgAuth, EvergreenApi
>> api = EvergreenApi.get_api(EvgAuth('your.username', '***'))
>> project = api.project_by_id('mongodb-mongo-master')
>> project.display_name
'MongoDB (master)'
```

Cli:

```bash
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
```

The `patch_from_diff` API requires the Evergreen CLI to be installed.
Add the following to the host's DOCKERFILE:

```bash
RUN wget https://evergreen.mongodb.com/clients/linux_amd64/evergreen
RUN chmod +x evergreen
ENV PATH="/project:$PATH"
```

You will need to provide an .evergreen.yml file with credentials to use the CLI. Assuming you are using the [web-app](https://github.com/10gen/helm-charts/tree/master/charts/web-app) chart this can be done by [mounting](https://kanopy.corp.mongodb.com/docs/getting_started/application_configuration/#configuration-filesvolumes) [kubernetes secrets](https://kanopy.corp.mongodb.com/docs/cheatsheet/#interacting-with-kubernetes-secrets) in your pod.

Store the secret in the cluster:

```bash
kubectl create secret generic <secret_name> --from-file .evergreen.yml --namespace <namespace>
```

In environments/deployment.yml configure the file to be mounted and linked to the correct location:

```yaml
volumeSecrets:
  - name: <secret_name>
    path: /etc/secrets
lifecycle:
  postStart:
    type: exec
    command:
      - /bin/sh
      - -c
      - ln -sf /etc/secrets/.evergreen.yml
```

## Documentation

You can find the documentation [here](https://evergreen-ci.github.io/evergreen.py/).

## Contributor's Guide

### Setting up a local development environment

#### Requirements

- Poetry 1.1 or later

You will need Evergreen credentials on your local machine to use this library or the attached CLI. You can authenticate in one of two ways: 

- *Deprecated soon* set up your credentials by following the link [here](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool). 

- Authenticate through kanopy-oidc. Please follow the installation instructions [here](https://docs.devprod.prod.corp.mongodb.com/evergreen/CLI#install-kanopy-oidc). You will be prompted to click on a link to authenticate. 

### Linting/formatting

This project uses [black](https://github.com/psf/black) and [isort](https://pycqa.github.io/isort/) for linting/formatting.

```bash
poetry run black src tests
poetry run isort src tests
```

### Running tests

```bash
poetry run pytest
```

There are a few tests that are slow running. These tests are not run by default, but can be included
by setting the env variable RUN_SLOW_TESTS to any value.

```
$ RUN_SLOW_TEST=1 poetry run pytest
```

To get code coverage information:

```
$ poetry run pytest --cov=src --cov-report=html
```

### Automatically running checks on commit

This project has [pre-commit](https://pre-commit.com/) configured. Pre-commit will run
configured checks at git commit time. To enable pre-commit on your local repository run:

```bash
$ poetry run pre-commit install
```

### Versioning

Before deploying a new version, please update the `CHANGELOG.md` file with a description of what
is being changed.

Deployment to [PyPi](https://pypi.org/project/evergreen.py/) are done automatically on merges to master.
In order to avoid overwriting a previous deploy, the version should be updated on all changes. The
[semver](https://semver.org/) versioning scheme should be used for determining the version number.

The version is found in the `pyproject.toml` file.

### Code Review

This project uses the GitHub merge queue. Click "Merge when ready" as soon as you'd like.

### Deployment

Deployment to [PyPi](https://pypi.org/project/evergreen.py/) is automatically triggered on merges to master.
