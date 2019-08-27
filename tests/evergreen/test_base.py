import pickle
from copy import copy

from evergreen.base import _BaseEvergreenObject


class TestPickleSupport(object):
    def test_can_pickle_copy_support(self, sample_task):
        """Tests that a copy of the base evergreen object can be pickled"""
        original = _BaseEvergreenObject(sample_task, None)
        task = copy(original)
        dump = pickle.dumps(task)
        unpickled = pickle.loads(dump)
        assert unpickled == original
