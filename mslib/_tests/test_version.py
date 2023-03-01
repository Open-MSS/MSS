# -*- coding: utf-8 -*-
"""

    mslib._tests.utils
    ~~~~~~~~~~~~~~~~~~

    This module provides common functions for MSS testing

    This file is part of MSS.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2022 by the MSS team, see AUTHORS.
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
from packaging.version import Version
from mslib import __version__


def test_version_string():
    Version(__version__)
    with pytest.raises():
        test_version_string()
