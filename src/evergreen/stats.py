# -*- encoding: utf-8 -*-
"""Stats representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_date_attrib


class TestStats(_BaseEvergreenObject):
    """Representation of an Evergreen test stats object."""

    test_file = evg_attrib('test_file')
    task_name = evg_attrib('task_name')
    variant = evg_attrib('variant')
    distro = evg_attrib('distro')
    evg_date_attrib('date')
    num_pass = evg_attrib('num_pass')
    num_fail = evg_attrib('num_fail')
    avg_duration_pass = evg_attrib('avg_duration_pass')

    def __init__(self, json, api):
        """
        Create an instance of a test stats object.

        :param json: json version of object.
        """
        super(TestStats, self).__init__(json, api)
