from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject

_EVG_DATE_FIELDS_IN_PATCH = frozenset([
    'create_time',
    'start_time',
    'finish_time',
])


class GithubPatchData(_BaseEvergreenObject):
    """Representation of github patch data in a patch object."""

    def __init__(self, json, api):
        """
        Create an instance of github patch data.

        :param json: json representing github patch data.
        :param api: instance of evergreen api object.
        """
        super(GithubPatchData, self).__init__(json, api)


class VariantsTasks(_BaseEvergreenObject):
    """Representation of a variants tasks object."""

    def __init__(self, json, api):
        """
        Create an instance of a variants tasks object.

        :param json: json representing variants tasks object.
        :param api: intance of the evergreen api object.
        """
        super(VariantsTasks, self).__init__(json, api)
        self._task_set = 0

    @property
    def tasks(self):
        """
        Retrieve the set of all tasks for this variant.

        :return: Set of all tasks for this variant.
        """
        if not self._task_set:
            self._task_set = set(self.json['tasks'])

        return self._task_set


class Patch(_BaseEvergreenObject):
    """
    Representation of an Evergreen patch.
    """

    def __init__(self, json, api):
        """
        Create an instance of an evergreen patch.

        :param json: json representing patch.
        """
        super(Patch, self).__init__(json, api)
        self._date_fields = _EVG_DATE_FIELDS_IN_PATCH
        self._variants_tasks = None
        self._variant_task_dict = None

    @property
    def github_patch_data(self):
        """
        Retrieve the github patch data for this patch.

        :return: Github Patch Data for this patch.
        """
        return GithubPatchData(self.json['github_patch_data'], self._api)

    @property
    def variants_tasks(self):
        """
        Retrieve the variants tasks for this patch.

        :return: variants tasks for this patch.
        """
        if not self._variants_tasks:
            self._variants_tasks = [VariantsTasks(vt, self._api)
                                    for vt in self.json['variants_tasks']]
        return self._variants_tasks

    def task_list_for_variant(self, variant):
        """
        Retrieve the list of tasks for the given variant.

        :param variant: name of variant to search for.
        :return: list of tasks belonging to the specified variant.
        """
        if not self._variant_task_dict:
            self._variant_task_dict = {vt.name: vt.tasks for vt in self.variants_tasks}
        return self._variant_task_dict[variant]

    def get_version(self):
        """
        Get version for this patch.

        :return: Version object.
        """
        return self._api.version_by_id(self.version)

    def __str__(self):
        return '{}: {}'.format(self.patch_id, self.description)
