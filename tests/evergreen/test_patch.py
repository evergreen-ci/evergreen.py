# -*- encoding: utf-8 -*-
"""Unit tests for src/evergreen/host.py."""
from __future__ import absolute_import

from evergreen.patch import Patch


class TestPatch(object):
    def test_get_attributes(self, sample_patch):
        patch = Patch(sample_patch, None)
        assert patch.description == sample_patch["description"]
        assert patch.version == sample_patch["version"]
        assert patch.github_patch_data.pr_number == sample_patch["github_patch_data"]["pr_number"]

    def test_variants_tasks(self, sample_patch):
        patch = Patch(sample_patch, None)
        assert len(patch.variants_tasks) == len(sample_patch["variants_tasks"])
        for vt, svt in zip(patch.variants_tasks, sample_patch["variants_tasks"]):
            assert vt.name == svt["name"]
            assert isinstance(vt.tasks, set)

    def test_task_list_for_variant(self, sample_patch):
        patch = Patch(sample_patch, None)
        sample_variant = sample_patch["variants_tasks"][0]
        variant_name = sample_variant["name"]
        assert patch.task_list_for_variant(variant_name) == set(sample_variant["tasks"])
