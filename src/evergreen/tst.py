# -*- encoding: utf-8 -*-
"""Test representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib


class Logs(_BaseEvergreenObject):
    """Representation of test logs from evergreen."""

    url = evg_attrib('url')
    line_num = evg_attrib('line_num')
    url_raw = evg_attrib('url_raw')
    log_id = evg_attrib('log_id')

    def __init__(self, json, api):
        """Create an instance of a Test log."""
        super(Logs, self).__init__(json, api)


class Tst(_BaseEvergreenObject):
    """
    Representation of a test object from evergreen.
    """

    task_id = evg_attrib('task_id')
    status = evg_attrib('status')
    test_file = evg_attrib('test_file')
    exit_code = evg_attrib('exit_code')
    start_time = evg_datetime_attrib('start_time')
    end_time = evg_datetime_attrib('end_time')

    def __init__(self, json, api):
        """Create an instance of a Test object."""
        super(Tst, self).__init__(json, api)

    @property
    def logs(self):
        """
        Get the log object for the given test.

        :return: log object for test.
        """
        return Logs(self.json['logs'], self._api)
