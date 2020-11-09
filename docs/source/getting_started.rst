*********************************
Getting started with evergreen.py
*********************************

Design Philosophy
=================

This project is meant to be a thin client around the `Evergreen REST API <https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage>`_. As such,
you can refer to the REST API for more detailed documentation.

Missing Fields
--------------

One of the goals of this project is to provide native python objects for working
with the API rather than working with raw JSON. This allows features like
autocomplete in modern editors. However, new fields can be introduced to the
data and updates to this project tend to lagging. Evergreen object does have a
``json`` attribute that can be used to access any properties not already
included.

.. code-block:: python

    project = evg_api.project_by_id("my-project")

    assert project.display_name == project.json["display_name"]

New Functionality
-----------------

Development of this project has mostly happened in a JIT (Just In Time)
fashion. The Evergreen API is constantly being added to, but a lot of the
new functionality has not been used in any python scripts. Thus parts of the
client may be missing or incomplete. If there is additional functionality you
would like added, feel free to put up a PR.

Getting an API object
=====================

The first step in using the API is to get an API object to work with. This can
be done with the ``get_api`` method.

.. code-block:: python

    from evergreen import EvergreenApi

    evg_api = EvergreenApi.get_api()

Many Evergreen endpoints require authentication. When creating an ``EvergreenApi``
object, you can pass credentials to use for authentication. There are a number
of way to do this.

Pass credentials directly
-------------------------

You can pass in credentials directly with an ``EvgAuth`` object:

.. code-block:: python

    from evergreen import EvergreenApi, EvgAuth

    evg_api = EvergreenApi.get_api(auth=EvgAuth(username="my_user", api_key="api_key"))

Pass credentials via a configuration file
-----------------------------------------

You can also pass credentials with a configuration file. The configuration file
should use the same format and location used the by the `evergreen command line tool <https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool>`_.

.. code-block:: python

    from evergreen import EvergreenApi

    evg_api = EvergreenApi.get_api(use_config_file=True)

You can also specify a location for the config file:

.. code-block:: python

    from evergreen import EvergreenApi

    evg_api = EvergreenApi.get_api(config_file="/path/to/config")

Special API Types
-----------------

We have occassionally seen intermittent failures from the Evergreen API. These
go away on retry. As a result, a ``RetryingEvergreenApi`` is provided that we
retry requests that failed with an HTTP Error. This will retry an API call
three times before failing.

It can be created just like an normal ``EvergreenApi``:

.. code-block:: python

    from evergreen import RetryingEvergreenApi

    evg_api = RetryingEvergreenApi.get_api()

After creating a ``RetryingEvergreenApi`` is can be treated just like a normal
``EvergreenApi`` object.

Session
-------

If you are making several calls to the API is a short amount of time, you may wish to create
a shared session for all the calls rather than a new session for each call. This can be done
with the `with_session` context manager.

.. code-block:: python

    from evergreen import EvergreenApi

    evg_api = EvergreenApi.get_api(use_config_file=True)
    with evg_api.with_session() as evg_session:
        evg_session.all_projects()
        evg_session.versions_by_project()
