# Evergreen.py

A client library for the Evergreen API written in python. Currently supports the V2 version of
the API. For more details, see https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage .

## Usage

```
>>> from evergreen.api import EvgAuth, EvergreenApi
>>> api = EvergreenApi.get_api(EvgAuth('david.bradford', '***'))
>>> project = api.project_by_id('mongodb-mongo-master')
>>> project.display_name
'MongoDB (master)'
```


## Testing

Tox is being used for multiversion testing. Tests are run on python 2.7 and 3.6. You should have
both of these installed locally. To run tests, install the requirements.txt and then run tox.

```
$ pip install -r requirements.txt
$ tox
```

To get code coverage information, you can run pytest directly.

```
$ pip install -r requirements.txt
$ pytest --cov=src --cov-report=html
```

This will generate an html coverage report in `htmlcov/` directory.
