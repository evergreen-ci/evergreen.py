# -*- encoding: utf-8 -*-

from evergreen.project_history import ProjectHistory


class TestProjectHistory(object):

    def test_deserialization(self, sample_project_history):
        project_history = ProjectHistory(sample_project_history, None)

        assert project_history.project == sample_project_history['project']

        version = project_history.versions[0]
        version_json = sample_project_history['versions'][0]

        assert version.version_id == version_json['version_id']
        assert version.author == version_json['author']
        assert version.revision == version_json['revision']
        assert version.message == version_json['message']

        build = version.builds[0]
        build_json_key, build_json = version_json['builds'].items()[0]

        assert build.build_id == build_json['build_id']
        assert build.build_name == build_json_key

        task = build.tasks[0]
        task_json_key, task_json = build_json['tasks'].items()[0]

        assert task.task_name == task_json_key
        assert task.status == task_json['status']
        assert task.task_id == task_json['task_id']
        assert task.time_taken == task_json['time_taken']
