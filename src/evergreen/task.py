# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from datetime import timedelta
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, List, Optional, TYPE_CHECKING

from evergreen.base import _BaseEvergreenObject, evg_attrib, evg_datetime_attrib

if TYPE_CHECKING:
    from evergreen.api import EvergreenApi
    from evergreen.tst import Tst  # noqa: F401

EVG_SUCCESS_STATUS = "success"
EVG_SYSTEM_FAILURE_STATUS = "system"
EVG_UNDISPATCHED_STATUS = "undispatched"

_EVG_DATE_FIELDS_IN_TASK = frozenset(
    ["create_time", "dispatch_time", "finish_time", "ingest_time", "scheduled_time", "start_time"]
)


class Artifact(_BaseEvergreenObject):
    """Representation of a task artifact from evergreen."""

    name = evg_attrib("name")
    url = evg_attrib("url")
    visibility = evg_attrib("visibility")
    ignore_for_fetch = evg_attrib("ignore_for_fetch")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """Create an instance of an evergreen task artifact."""
        super(Artifact, self).__init__(json, api)


class StatusScore(IntEnum):
    """Integer score of the task status."""

    SUCCESS = 1
    FAILURE = 2
    FAILURE_SYSTEM = 3
    FAILURE_TIMEOUT = 4
    UNDISPATCHED = 5

    @classmethod
    def get_task_status_score(cls, task: "Task") -> "StatusScore":
        """
        Retrieve the status score based on the task status.

        :return: Status score.
        """
        if task.is_success():
            return StatusScore.SUCCESS
        if task.is_undispatched():
            return StatusScore.UNDISPATCHED
        if task.is_timeout():
            return StatusScore.FAILURE_TIMEOUT
        if task.is_system_failure():
            return StatusScore.FAILURE_SYSTEM
        return StatusScore.FAILURE


class StatusDetails(_BaseEvergreenObject):
    """Representation of a task status details from evergreen."""

    status = evg_attrib("status")
    type = evg_attrib("type")
    desc = evg_attrib("desc")
    timed_out = evg_attrib("timed_out")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """Create an instance of an evergreen task status details."""
        super(StatusDetails, self).__init__(json, api)


class Task(_BaseEvergreenObject):
    """Representation of an Evergreen task."""

    activated = evg_attrib("activated")
    activated_by = evg_attrib("activated_by")
    build_id = evg_attrib("build_id")
    build_variant = evg_attrib("build_variant")
    create_time = evg_datetime_attrib("create_time")
    depends_on = evg_attrib("depends_on")
    dispatch_time = evg_datetime_attrib("dispatch_time")
    display_name = evg_attrib("display_name")
    display_only = evg_attrib("display_only")
    distro_id = evg_attrib("distro_id")
    est_wait_to_start_ms = evg_attrib("est_wait_to_start_ms")
    estimated_cost = evg_attrib("estimated_cost")
    execution = evg_attrib("execution")
    execution_tasks = evg_attrib("execution_tasks")
    expected_duration_ms = evg_attrib("expected_duration_ms")
    finish_time = evg_datetime_attrib("finish_time")
    generate_task = evg_attrib("generate_task")
    generated_by = evg_attrib("generated_by")
    host_id = evg_attrib("host_id")
    ingest_time = evg_datetime_attrib("ingest_time")
    mainline = evg_attrib("mainline")
    order = evg_attrib("order")
    project_id = evg_attrib("project_id")
    priority = evg_attrib("priority")
    restarts = evg_attrib("restarts")
    revision = evg_attrib("revision")
    scheduled_time = evg_datetime_attrib("scheduled_time")
    start_time = evg_datetime_attrib("start_time")
    status = evg_attrib("status")
    task_group = evg_attrib("task_group")
    task_group_max_hosts = evg_attrib("task_group_max_hosts")
    task_id = evg_attrib("task_id")
    time_taken_ms = evg_attrib("time_taken_ms")
    version_id = evg_attrib("version_id")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """Create an instance of an evergreen task."""
        super(Task, self).__init__(json, api)
        self._logs_map: Optional[Dict[Any, Any]] = None

    @property
    def artifacts(self) -> List[Artifact]:
        """
        Retrieve the artifacts for the given task.

        :return: List of artifacts.
        """
        if not self.json.get("artifacts"):
            return []
        return [Artifact(artifact, self._api) for artifact in self.json["artifacts"]]

    @property
    def log_map(self) -> Dict:
        """
        Retrieve a dict of all the logs.

        :return: Dictionary of the logs.
        """
        if not self._logs_map:
            self._logs_map = {key: value for key, value in self.json["logs"].items()}
        return self._logs_map

    def retrieve_log(self, log_name: str, raw: bool = False) -> str:
        """
        Retrieve the contents of the specified log.

        :param log_name: Name of log to retrieve.
        :param raw: Retrieve raw version of log.
        :return: Contents of the specified log.
        """
        return self._api.retrieve_task_log(self.log_map[log_name], raw)

    def stream_log(self, log_name: str) -> Iterable[str]:
        """
        Retrieve an iterator of a streamed log contents for the given log.

        :param log_name: Log to stream.
        :return: Iterable log contents.
        """
        return self._api.stream_log(self.log_map[log_name])

    @property
    def status_details(self) -> StatusDetails:
        """
        Retrieve the status details for the given task.

        :return: Status details.
        """
        return StatusDetails(self.json["status_details"], self._api)

    def get_status_score(self) -> StatusScore:
        """
        Retrieve the status score enum for the given task.

        :return: Status score.
        """
        return StatusScore.get_task_status_score(self)

    def get_execution(self, execution: int) -> Optional["Task"]:
        """
        Get the task info for the specified execution.

        :param execution: Index of execution.
        :return: Task info for specified execution.
        """
        if self.execution == execution:
            return self

        if "previous_executions" in self.json:
            for task in self.json["previous_executions"]:
                if task["execution"] == execution:
                    return Task(task, self._api)

        return None

    def get_execution_or_self(self, execution: int) -> "Task":
        """
        Get the specified execution if it exists.

        If the specified execution does not exist, return self.

        :param execution: Index of execution.
        :return: Task info for specified execution or self.
        """
        task_execution = self.get_execution(execution)
        if task_execution:
            return task_execution
        return self

    def wait_time(self) -> Optional[timedelta]:
        """
        Get the time taken until the task started running.

        :return: Time taken until task started running.
        """
        if self.start_time and self.ingest_time:
            return self.start_time - self.ingest_time
        return None

    def wait_time_once_unblocked(self) -> Optional[timedelta]:
        """
        Get the time taken until the task started running.

        Once it is unblocked by task dependencies.

        :return: Time taken until task started running.
        """
        if self.start_time and self.scheduled_time:
            return self.start_time - self.scheduled_time
        return None

    def is_success(self) -> bool:
        """
        Whether task was successful.

        :return: True if task was successful.
        """
        return self.status == EVG_SUCCESS_STATUS

    def is_undispatched(self) -> bool:
        """
        Whether the task was undispatched.

        :return: True is task was undispatched.
        """
        return self.status == EVG_UNDISPATCHED_STATUS

    def is_system_failure(self) -> bool:
        """
        Whether task resulted in a system failure.

        :return: True if task was a system failure.
        """
        if not self.is_success() and self.status_details and self.status_details.type:
            return self.status_details.type == EVG_SYSTEM_FAILURE_STATUS
        return False

    def is_timeout(self) -> bool:
        """
        Whether task results in a timeout.

        :return: True if task was a timeout.
        """
        if not self.is_success() and self.status_details and self.status_details.timed_out:
            return self.status_details.timed_out
        return False

    def is_active(self) -> bool:
        """
        Determine if the given task is active.

        :return: True if task is active.
        """
        return self.scheduled_time and not self.finish_time

    def get_tests(
        self, status: Optional[str] = None, execution: Optional[int] = None
    ) -> List["Tst"]:
        """
        Get the test results for this task.

        :param status: Only return tests with the given status.
        :param execution: Return results for specified execution, if specified.
        :return: List of test results for the task.
        """
        return self._api.tests_by_task(
            self.task_id,
            status=status,
            execution=self.execution if execution is None else execution,
        )

    def get_execution_tasks(
        self, filter_fn: Optional[Callable[["Task"], bool]] = None
    ) -> Optional[List["Task"]]:
        """
        Get a list of execution tasks associated with this task.

        If this is a display task, return the tasks execution tasks associated with it. 
        If this is not a display task, returns None.

        :param filter_fn: Function to filter returned results.
        :return: List of execution tasks.
        """
        if self.display_only:
            execution_tasks = [
                self._api.task_by_id(task_id, fetch_all_executions=True)
                for task_id in self.execution_tasks
            ]

            execution_tasks = [
                task.get_execution_or_self(self.execution) for task in execution_tasks
            ]

            if filter_fn:
                return [task for task in execution_tasks if filter_fn(task)]
            return execution_tasks

        return None

    def __repr__(self) -> str:
        """
        Get a string representation of Task for debugging purposes.

        :return: String representation of Task.
        """
        return "Task({id})".format(id=self.task_id)
