# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility functions for mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi

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

from mslib.mscolab.sockets_manager import fm
def get_recent_pid(user):
    projects = fm.list_projects(user)
    p_id = projects[-1]["p_id"]
    return p_id
