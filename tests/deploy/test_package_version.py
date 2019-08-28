import os
import sys

import pytest
from pylibversion import lookup_latest_version_in_pypi

import evergreen


class TestPackageVersion:
    @pytest.mark.skipif(
        not os.environ.get('RUN_VERSION_TESTS') or sys.version_info[0] < 3,
        reason="Don't check the version string for local testing"
    )
    def test_version_is_updated(self):
        module_name = "evergreen.py"
        pypi_version = lookup_latest_version_in_pypi(module_name)
        my_version = evergreen.__version__

        assert my_version != pypi_version
