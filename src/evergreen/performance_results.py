# -*- encoding: utf-8 -*-
"""Performance results representation of evergreen."""
from __future__ import absolute_import

import copy

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_short_datetime_attrib, \
    evg_datetime_attrib
from evergreen.util import parse_evergreen_datetime


class PerformanceTestResult(_BaseEvergreenObject):
    """Representation of a test result from Evergreen."""
    thread_level = evg_attrib('thread_level')
    operations_per_second = evg_attrib('ops_per_sec_values')
    mean_operations_per_second = evg_attrib('ops_per_sec')

    def __init__(self, json, api):
        """Create an instance of a test result."""
        super(PerformanceTestResult, self).__init__(json, api)


class PerformanceTestRun(_BaseEvergreenObject):
    """Representation of a test run from Evergreen."""
    workload = evg_attrib('workload')
    test_name = evg_attrib('name')

    def __init__(self, test_result, api):
        """Create an instance of a test run."""
        super(PerformanceTestRun, self).__init__(test_result, api)

        # Microbenchmarks stores the 'start' and 'end' time of the test in the inner 'results' field
        # while sys-perf stores it in the outer 'results' field.
        self.start = parse_evergreen_datetime(
            test_result.get('start', test_result['results']['start']))
        self.end = parse_evergreen_datetime(
            test_result.get('end', test_result['results']['end']))
        # Microbenchmarks does not produce a 'workload' field. We need to fill in the 'workload'
        # field for microbenchmark points in order to query on 'workload'.
        self.maximum_thread_level, self.maximum_operations_per_second = _get_max_ops_per_sec(
            test_result)

    @property
    def test_results(self):
        if self.maximum_operations_per_second is None:
            return None
        return _get_performance_results(self.json, self._api)


class PerformanceTestBatch(_BaseEvergreenObject):
    """Representation of a batch of tests from Evergreen."""
    start = evg_datetime_attrib('start')
    end = evg_datetime_attrib('end')
    storage_engine = evg_attrib('storageEngine')
    errors = evg_attrib('errors')

    def __init__(self, json, api, parent):
        """Create an instance of a batch of tests"""
        super(PerformanceTestBatch, self).__init__(json, api)
        self.parent = parent

    @property
    def test_runs(self):
        return [PerformanceTestRun(item, self._api) for item in self.json['results']]

    def test_runs_matching(self, tests):
        return [item for item in self.test_runs if
                _is_run_matching(item, tests)]


class PerformanceData(_BaseEvergreenObject):
    """Representation of performance data from Evergreen."""
    name = evg_attrib('name')
    project_id = evg_attrib('project_id')
    task_name = evg_attrib('task_name')
    task_id = evg_attrib('task_id')
    variant = evg_attrib('variant')
    version_id = evg_attrib('version_id')
    revision = evg_attrib('revision')
    order = evg_attrib('order')
    tag = evg_attrib('tag')
    create_time = evg_short_datetime_attrib('create_time')

    def __init__(self, json, api):
        """Create an instance of performance data"""
        super(PerformanceData, self).__init__(json, api)

    @property
    def test_batch(self):
        return PerformanceTestBatch(self.json['data'], self._api, self)


def _get_performance_results(test_result, api):
    """
    Extract and sort the thread level and respective results from the raw data file from Evergreen.
    See below for an example of the resulting format:

        [
            {
                'thread_level': '1',
                'ops_per_sec': 500,
                'ops_per_sec': [
                    500
                ]
            },
            {
                'thread_level: '2',
                'ops_per_sec': 700,
                'ops_per_sec': [
                    700
                ]
            }
        ]

    :param dict test_result: All the test results from the raw data file from Evergreen.
    :return: A list of dictionaries with test results organized by thread level.
    """
    thread_levels = []
    for thread_level, result in test_result['results'].items():
        if isinstance(result, dict):
            this_result = copy.deepcopy(result)
            this_result.pop('error_values', None)
            this_result.update({'thread_level': thread_level})
            test_result = PerformanceTestResult(this_result, api)
            thread_levels.append(test_result)
    return sorted(thread_levels, key=lambda k: k.thread_level)


def _get_max_ops_per_sec(test_result):
    """
    For a given set of test results, find and return the maximum operations per second metric and
    its respective thread level.

    :param dict test_result: All the test results from the raw data file from Evergreen.
    :return: The maximum operations per second found and its respective thread level.
    :rtype: tuple(int, int).
    """
    max_ops_per_sec = None
    max_thread_level = None
    results = test_result['results']
    for key, thread_level in results.items():
        if not key.isdigit():
            continue
        if max_ops_per_sec is None or max_ops_per_sec < thread_level['ops_per_sec']:
            max_ops_per_sec = thread_level['ops_per_sec']
            max_thread_level = int(key)
    return max_thread_level, max_ops_per_sec


def _is_run_matching(test_run, tests):
    """
    Determine if the given test_run matches a set of tests.

    :param test_run: test_run to check.
    :param tests: List of tests to upload.
    :return: True if the test_run contains relevant data.
    """
    if tests is not None and test_run.test_name not in tests:
        return False

    if test_run.start is None:
        return False

    if all(result.operations_per_second is None for result in test_run.test_results):
        return False

    return True
