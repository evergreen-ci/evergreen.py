

class EvergreenException(Exception):
    """An exception coming from the evergreen client."""

    def __init__(self, msg=None):
        """
        Create a new exception instance.
        :param msg: Message describing exception.
        """
        if not msg:
            msg = 'Exception in evergreen client'

        super(EvergreenException, self).__init__(msg)


class MetricsException(EvergreenException):
    """An exception with metrics collection."""

    def __init__(self, msg=None):
        """
        Create a new exception instance.

        :param msg: Message describing exception.
        """
        if not msg:
            msg = 'Exception in metrics collection'

        super(MetricsException, self).__init__(msg)


class ActiveTaskMetricsException(MetricsException):
    """An exception when a task is in progress during metrics collection."""

    def __init__(self, task, msg=None):
        """
        Create a new exception instance.

        :param task: Task in progress.
        :param msg: Message describing exception.
        """
        if not msg:
            msg = 'Exception in metrics collection'

        super(MetricsException, self).__init__(msg)

        self.task = task
