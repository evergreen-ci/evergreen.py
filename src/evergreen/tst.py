# -*- encoding: utf-8 -*-
"""Test representation of evergreen."""
from __future__ import absolute_import

from typing import TYPE_CHECKING, Any, Dict, Iterable

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib

if TYPE_CHECKING:
    from evergreen.api import EvergreenApi


class Logs(_BaseEvergreenObject):
    """Representation of test logs from evergreen."""

    line_num = evg_attrib("line_num")
    url = evg_attrib("url")
    url_parsley = evg_attrib("url_parsley")
    url_raw = evg_attrib("url_raw")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """Create an instance of a Test log."""
        super(Logs, self).__init__(json, api)

    def stream(self) -> Iterable[str]:
        """
        Retrieve an iterator of the streamed contents of this log.

        :return: Iterable to stream contents of log.
        """
        return self._api.stream_log(self.url_raw)


class Tst(_BaseEvergreenObject):
    """Representation of a test object from evergreen."""

    end_time = evg_datetime_attrib("end_time")
    group_id = evg_attrib("group_id")
    start_time = evg_datetime_attrib("start_time")
    status = evg_attrib("status")
    task_id = evg_attrib("task_id")
    test_file = evg_attrib("test_file")
    test_id = evg_attrib("test_id")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """Create an instance of a Test object."""
        super(Tst, self).__init__(json, api)

    @property
    def logs(self) -> Logs:
        """
        Get the log object for the given test.

        :return: log object for test.
        """
        return Logs(self.json["logs"], self._api)
