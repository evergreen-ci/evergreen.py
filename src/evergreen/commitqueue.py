# -*- encoding: utf-8 -*-
"""Commit Queue representation of evergreen."""
from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject, evg_attrib


class CommitQueueItem(_BaseEvergreenObject):
    """Representation of an entry in a commit queue."""
    issue = evg_attrib('issue')
    modules = evg_attrib('modules')

    def __init__(self, json, api):
        super(CommitQueueItem, self).__init__(json, api)


class CommitQueue(_BaseEvergreenObject):
    """Representation of a commit queue from evergreen."""
    queue_id = evg_attrib('queue_id')

    def __init__(self, json, api):
        """
        Create an instance of a commit queue from evergreen json.

        :param json: Evergreen json representation of commit queue.
        :param api: Evergreen api object.
        """
        super(CommitQueue, self).__init__(json, api)

    @property
    def queue(self):
        """
        Retrieve the queue for this commit queue.
        :return: Queue of commits in the commit queue.
        """
        if not self.json['queue']:
            return []
        return [CommitQueueItem(item, self._api) for item in self.json['queue']]
