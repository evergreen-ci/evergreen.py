# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime

from evergreen.version import Version


class TestVersion(object):
    def test_get_attributes(self, sample_version):
        version = Version(sample_version, None)
        assert version.version_id == sample_version['version_id']

    def test_dates_are_correct(self, sample_version):
        version = Version(sample_version, None)
        assert isinstance(version.create_time, datetime)

    def test_build_variant_status(self, sample_version):
        version = Version(sample_version, None)
        assert len(sample_version['build_variants_status']) == len(version.build_variants_status)
