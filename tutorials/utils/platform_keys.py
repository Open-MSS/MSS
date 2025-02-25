"""
    msui.tutorials.utils.platform_keys
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Includes platform-specific modules

    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2024 by the MSS team, see AUTHORS.
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
import sys


def platform_keys():
    """
    Returns platform specific key mappings.

    Returns:
        A tuple containing the key mappings for the current platform.

    Note:
        The key mappings returned depend on the value of `sys.platform`.
        For Linux, the return values are ('ctrl', 'enter', 'winleft', 'altleft').
        For Windows, the return values are ('ctrl', 'enter', 'win', 'alt').
        For macOS, the return values are ('command', 'return').

    Example:
        ctrl, enter, win, alt = platform_keys()
    """
    #  sys.platform specific keyse
    if sys.platform == 'linux' or sys.platform == 'linux2':
        enter = 'enter'
        win = 'winleft'
        ctrl = 'ctrl'
        alt = 'altleft'
    elif sys.platform == 'win32':
        enter = 'enter'
        win = 'win'
        ctrl = 'ctrl'
        alt = 'alt'
    elif sys.platform == 'darwin':
        enter = 'return'
        ctrl = 'control'
        alt = 'option'
        win = 'command'
    return ctrl, enter, win, alt
