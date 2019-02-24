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
