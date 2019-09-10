# -*- encoding: utf-8 -*-
import random
from copy import copy

from evergreen.performance_results import PerformanceData
from evergreen.util import parse_evergreen_datetime, parse_evergreen_short_datetime


class TestPerformanceResults(object):
    def test_adds_max_thread_level(self, sample_performance_results):
        performance_data = PerformanceData(sample_performance_results, None)
        results = performance_data.test_batch.test_runs[0].test_results
        results.reverse()
        assert results[0].thread_level == 'max'

    def test_sorting(self, sample_performance_results):
        duplicate = copy(sample_performance_results)
        data = list(sample_performance_results['data']['results'][0]['results'].items())
        random.shuffle(data)
        duplicate['data']['results'][0]['results'] = {key: val for key, val in data}
        performance_data = PerformanceData(duplicate, None)
        results = performance_data.test_batch.test_runs[0].test_results
        thread_levels = [item.thread_level for item in results if item.thread_level != 'max']
        assert thread_levels == sorted(thread_levels)

    def test_deserialization(self, sample_performance_results):
        performance_data = PerformanceData(sample_performance_results, None)

        assert performance_data.name == sample_performance_results['name']
        assert performance_data.task_name == sample_performance_results['task_name']
        assert performance_data.project_id == sample_performance_results['project_id']
        assert performance_data.task_id == sample_performance_results['task_id']
        assert performance_data.build_id == sample_performance_results['build_id']
        assert performance_data.variant == sample_performance_results['variant']
        assert performance_data.version_id == sample_performance_results['version_id']
        assert performance_data.create_time == parse_evergreen_short_datetime(
            sample_performance_results['create_time'])
        assert performance_data.is_patch == sample_performance_results['is_patch']
        assert performance_data.order == sample_performance_results['order']
        assert performance_data.revision == sample_performance_results['revision']
        assert performance_data.tag == sample_performance_results['tag']

        test_batch = performance_data.test_batch
        test_batch_json = sample_performance_results['data']

        assert test_batch.start == parse_evergreen_datetime(test_batch_json['start'])
        assert test_batch.end == parse_evergreen_datetime(test_batch_json['end'])
        assert test_batch.errors == test_batch_json['errors']
        assert test_batch.storage_engine == test_batch_json['storageEngine']

        test_run = test_batch.test_runs[0]
        test_run_json = test_batch_json['results'][0]

        assert test_run.start == parse_evergreen_datetime(
            test_run_json['start'] if 'start' in test_run_json else test_run_json['results'][
                'start'])
        assert test_run.end == parse_evergreen_datetime(
            test_run_json['end'] if 'end' in test_run_json else test_run_json['results'][
                'end'])
        assert test_run.name == test_run_json['name']
        assert test_run.workload == test_run_json[
            'workload'] if 'workload' in test_run_json else 'microbenchmarks'
        assert test_run.results == test_run_json['results']

        test_result = test_run.test_results[0]
        test_result_json = test_run_json['results']['1']

        assert test_result.measurement == 'ops_per_sec'
        assert test_result.mean_value == test_result_json['ops_per_sec']
        assert test_result.recorded_values == test_result_json['ops_per_sec_values']
        assert test_result.thread_level == '1'

    def test_filtering_of_tests(self, sample_performance_results):
        tests = ['Aggregation.CountsFullCollection']
        performance_data = PerformanceData(sample_performance_results, None)
        all_runs = performance_data.test_batch.test_runs
        selected_runs = performance_data.test_batch.test_runs_matching(tests)

        assert all(item.test_name in tests for item in selected_runs)
        assert not all(item.test_name in tests for item in all_runs)
