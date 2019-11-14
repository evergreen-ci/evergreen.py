# -*- encoding: utf-8 -*-
"""Performance results representation of evergreen."""
from __future__ import absolute_import

from copy import copy

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_short_datetime_attrib


class PerformanceTestResult(_BaseEvergreenObject):
    """Representation of a test result from Evergreen."""
    thread_level = evg_attrib('thread_level')
    recorded_values = evg_attrib('recorded_values')
    mean_value = evg_attrib('mean_value')
    measurement = evg_attrib('measurement')

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

    @property
    def start(self):
        """Get the start time for the given test run."""
        # Microbenchmarks stores the 'start' and 'end' time of the test in the inner 'results' field
        # while sys-perf stores it in the outer 'results' field.
        # Also, the format of start varies depending on what generated the results.
        return self.json.get('start', self.json.get('results', {}).get('start'))

    @property
    def end(self):
        """Get the start time for the given test run."""
        # Microbenchmarks stores the 'start' and 'end' time of the test in the inner 'results' field
        # while sys-perf stores it in the outer 'results' field.
        # Also, the format of end varies depending on what generated the results.
        return self.json.get('end', self.json.get('results', {}).get('end'))

    @property
    def test_results(self):
        """Get the performance test results for this run."""
        return [PerformanceTestResult(item, self._api)
                for item in _format_performance_results(self.json['results'])]


class PerformanceTestBatch(_BaseEvergreenObject):
    """Representation of a batch of tests from Evergreen."""
    start = evg_attrib('start')
    end = evg_attrib('end')
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

    def __repr__(self):
        """
        String representation of PerformanceData for debugging purposes.

        :return: String representation of PreformanceData.
        """
        return "PerformanceData({id})".format(id=self.task_id)


def _format_performance_results(results):
    """
    Extract and sort the thread level and respective results from the raw data file from Evergreen,
    adding max result entries as appropriate.
    See below for an example of the transformation:
    Before:
    {
        "16":{
            "95th_read_latency_us":4560.0,
            "95th_read_latency_us_values":[
                4560.0
            ],
            "99th_read_latency_us":9150.0,
            "99th_read_latency_us_values":[
                9150.0
            ],
            "average_read_latency_us":1300.0,
            "average_read_latency_us_values":[
                1300.0
            ],
            "ops_per_sec":1100.0,
            "ops_per_sec_values":[
                1100.0
            ]
        },
        "8":{
            "95th_read_latency_us":4500.0,
            "95th_read_latency_us_values":[
                4000.0,
                5000.0
            ],
            "99th_read_latency_us":10000.0,
            "99th_read_latency_us_values":[
                10000.0
            ],
            "average_read_latency_us":1300.0,
            "average_read_latency_us_values":[
                1300.0
            ],
            "ops_per_sec":1100.0,
            "ops_per_sec_values":[
                1100.0
            ]
        }
    }
    After:
    [
        {
            'thread_level': '16',
            'mean_value': 4560.0,
            'recorded_values': [
                4560.0
            ],
            'measurement': '95th_read_latency_us'
        },
        {
            'thread_level': '16',
            'mean_value': 9150.0,
            'recorded_values': [
                9150.0
            ],
            'measurement': '99th_read_latency_us'
        },
        {
            'thread_level': '16',
            'mean_value': 1300.0,
            'recorded_values': [
                1300.0
            ],
            'measurement': 'average_read_latency_us'
        },
        {
            'thread_level': '16',
            'mean_value': 1100.0,
            'recorded_values': [
                1100.0
            ],
            'measurement': 'ops_per_sec'
        },
        {
            'thread_level': '8',
            'mean_value': 4500.0,
            'recorded_values': [
                4000.0,
                5000.0
            ],
            'measurement': '95th_read_latency_us'
        },
        {
            'thread_level': '8',
            'mean_value': 10000.0,
            'recorded_values': [
                10000.0
            ],
            'measurement': '99th_read_latency_us'
        },
        {
            'thread_level': '8',
            'mean_value': 1300.0,
            'recorded_values': [
                1300.0
            ],
            'measurement': 'average_read_latency_us'
        },
        {
            'thread_level': '8',
            'mean_value': 1100.0,
            'recorded_values': [
                1100.0
            ],
            'measurement': 'ops_per_sec'
        },
        {
            'thread_level': 'max',
            'mean_value': 4560.0,
            'recorded_values': [
                4560.0
            ],
            'measurement': '95th_read_latency_us'
        },
        {
            'thread_level': 'max',
            'mean_value': 10000.0,
            'recorded_values': [
                10000.0
            ],
            'measurement': '99th_read_latency_us'
        },
        {
            'thread_level': 'max',
            'mean_value': 1300.0,
            'recorded_values': [
                1300.0
            ],
            'measurement': 'average_read_latency_us'
        },
        {
            'thread_level': 'max',
            'mean_value': 1100.0,
            'recorded_values': [
                1100.0
            ],
            'measurement': 'ops_per_sec'
        }
    ]

    :param dict results: All the test results from the raw data file from Evergreen.
    :return: A list of PerformanceTestResults with test results organized by thread level.
    """
    # Sort as integers
    thread_levels = sorted(int(key) for key in results.keys() if key.isdigit())
    # Cast back to string
    thread_levels = [str(entry) for entry in thread_levels]
    performance_results = []
    maxima = {}

    for thread_level in thread_levels:
        thread_results = results[thread_level]
        measurement_names = [key for key in thread_results.keys() if 'values' not in key]
        for measurement in measurement_names:
            if measurement not in maxima:
                maxima[measurement] = None
            formatted = {
                'thread_level': thread_level,
                'mean_value': thread_results[measurement],
                'recorded_values': thread_results[measurement + '_values'],
                'measurement': measurement
            }
            performance_results.append(formatted)

            if maxima[measurement] is None or \
                    maxima[measurement]['mean_value'] < formatted['mean_value']:
                max_copy = copy(formatted)
                max_copy['thread_level'] = 'max'
                maxima[measurement] = max_copy

    return performance_results + list(maxima.values())


def _is_run_matching(test_run, tests):
    """
    Determine if the given test_run.json matches a set of tests.

    :param test_run: test_run.json to check.
    :param tests: List of tests to upload.
    :return: True if the test_run.json contains relevant data.
    """
    if tests is not None and test_run.test_name not in tests:
        return False

    if test_run.start is None:
        return False

    if all(result.mean_value is None for result in test_run.test_results):
        return False

    return True
