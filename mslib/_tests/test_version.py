import pytest
from packaging.version import Version, parse
from mslib import __version__


def test_version_string_setuptools():
    Version(__version__)

    def do_test():
        with pytest.raises():
            test_version_string_setuptools()
