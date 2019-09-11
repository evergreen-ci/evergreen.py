# Changelog

## 0.6.9 - 2019-09-11
- Remove pylibversion dependency in setup.

## 0.6.7 - 2019-09-06
- Fix issue with pip install.

## 0.6.6 - 2019-09-05
- Add support for metrics not reporting operations per second

## 0.6.5 - 2019-09-04
- Add CD support from evergreen.

## 0.6.4 - 2019-08-28
- Removed after_date default on task reliability.
- Updated task reliability documentation.

## 0.6.3 - 2019-08-27
- Supported multiprocessing use cases by implementing pickle support

## 0.6.2 - 2019-08-22
- Handle passed config file
- Remove broken project history API

## 0.6.1 - 2019-08-21
- Handle versions with empty`build_variants_status`.

## 0.6.0 - 2019-08-20
- Use new signal_processing supporting endpoints.

## 0.5.0 - 2019-08-14
- Add lazy versions by project endpoint.

## 0.4.1 - 2019-08-14
- Add task stats support.
- Add task reliability support.
- Support reading api_server_host from .evergreen.yml.

## 0.4.0 - 2019-07-30
- Use new commit_queue endpoints.

## 0.3.9 - 2019-07-15
- Update requests version.

## 0.3.8 - 2019-07-15
- Improved logging with structlog.

## 0.3.7 - 2019-07-11
- Better handle builds complete.

## 0.3.6 - 2019-07-11
- Watch for empty builds.

## 0.3.5 - 2019-07-11
- Account for undispatched builds.

## 0.3.4 - 2019-07-11
- Check builds are activated for metrics.

## 0.3.3 - 2019-07-11
- Relax version metrics check.

## 0.3.2 - 2019-06-27
- Add a retrying API.

## 0.3.1 - 2019-06-26
- Add task filter for metrics.

## 0.3.0 - 2019-06-24
- Simplified Metrics API.

## 0.2.3 - 2019-06-22
- Better metrics support.

## 0.2.2 - 2019-06-21
- Add metrics.
- Add network timeout support.

## 0.2.1 - 2019-06-20
- Add /distros support.

## 0.2.0 - 2019-06-16
- Change command line to evg-api.
- Add support for yaml and json command line output.
- Bug fixes.

## 0.1.16 - 2019-06-03
- Add endpoint that returns the wait time between dependencies being fulfilled and start of task

## 0.1.15 - 2019-05-31
- Add endpoint to query commit-queue.

## 0.1.14 - 2019-05-01
- Support for specifying a config file.

## 0.1.13 - 2019-04-18
- Add endpoints to get task logs.

## 0.1.12 - 2019-04-05
- Don't use current directory to search for evergreen config.

## 0.1.11 - 2019-03-29
- Improvements to version object.

## 0.1.10 - 2019-03-29
- Add attributes to evergreen objects.

## 0.1.9 - 2019-03-28
- Add basic task endpoints.
