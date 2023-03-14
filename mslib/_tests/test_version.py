# -*- coding: utf-8 -*-
"""

    mslib._tests.test_version
    ~~~~~~~~~~~~~~~~~~

    This module provides a test for the version string

    This file is part of MSS.

    :copyright: Copyright 2023 rootxrishabh
    :copyright: Copyright 2023 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import pytest
import packaging

from mslib import __version__


def test_version_string():
    try:
        packaging.version.Version(__version__)
    except packaging.version.InvalidVersion:
        pytest.fail("Version parsing fails")
