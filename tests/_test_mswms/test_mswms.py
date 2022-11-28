# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_mswms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.msui

    This file is part of MSS.

    :copyright: Copyright 2022 Reimar Bauer
    :copyright: Copyright 2022-2022 by the MSS team, see AUTHORS.
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


import mock
import argparse
import pytest
from mslib.mswms import mswms


class _Application():
    """ dummy to skip starting the wms server"""
    @staticmethod
    def run(host, port):
        pass


@mock.patch("mslib.mswms.mswms.application", _Application)
def test_main():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with mock.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                        return_value=argparse.Namespace(plot_types=None, version=True)):
            mswms.main()
        assert pytest_wrapped_e.typename == "SystemExit"

    with mock.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                    return_value=argparse.Namespace(plot_types=None, version=False, update=False, gallery=False,
                                                    debug=False, logfile=None, action=None,
                                                    host=None, port=None)):
        mswms.main()
    assert pytest_wrapped_e.typename == "SystemExit"
