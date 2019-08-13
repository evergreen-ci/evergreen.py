# -*- encoding: utf-8 -*-
"""Performance results representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib


class PerformanceResult(_BaseEvergreenObject):
    """Representation of a single performance result from evergreen"""
    start = evg_datetime_attrib('start')
    end = evg_datetime_attrib('end')
    name = evg_attrib('name')
    workload = evg_attrib('workload')
    results = evg_attrib('results')

    def __init__(self, json, api):
        """Create an instance of performance result data."""
        super(PerformanceResult, self).__init__(json, api)


class PerformanceResultData(_BaseEvergreenObject):
    """Representation of performance result data from evergreen."""

    storage_engine = evg_attrib('storageEngine')
    # Legacy support
    storageEngine = evg_attrib('storageEngine')

    def __init__(self, json, api):
        """Create an instance of performance result data."""
        super(PerformanceResultData, self).__init__(json, api)

    @property
    def results(self):
        """
        Get the actual results.
        :return: the performance results.
        """
        return [PerformanceResult(point) for point in self.json['results']]


class PerformanceResults(_BaseEvergreenObject):
    """
    Representation of a set of performance results from evergreen.
    """
    name = evg_attrib('name')
    task_name = evg_attrib('task_name')
    project_id = evg_attrib('project_id')
    task_id = evg_attrib('task_id')
    build_id = evg_attrib('build_id')
    variant = evg_attrib('variant')
    version_id = evg_attrib('version_id')
    create_time = evg_datetime_attrib('create_time')
    is_patch = evg_attrib('is_patch')
    order = evg_attrib('order')
    revision = evg_attrib('revision')
    tag = evg_attrib('tag')

    def __init__(self, json, api):
        """Create an instance of a perfomance results object."""
        super(PerformanceResults, self).__init__(json, api)

    @property
    def data(self):
        """
        Get the performance result data.

        :return: performance result data.
        """
        return PerformanceResultData(self.json['data'], self._api)
