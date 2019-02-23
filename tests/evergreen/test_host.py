from __future__ import absolute_import

from evergreen.host import Host


class TestHost(object):
    def test_get_attributes(self, sample_host):
        host = Host(sample_host, None)
        assert host.status == sample_host['status']
        assert host.host_id == sample_host['host_id']

    def test_running_task(self, sample_host):
        host = Host(sample_host, None)
        running_task = host.running_task
        assert running_task.task_id == sample_host['running_task']['task_id']
