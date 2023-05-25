# -*- coding: utf-8 -*-
"""

    mslib.mscolab.message_type.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import enum


class MessageType(enum.IntEnum):
    TEXT = 0
    SYSTEM_MESSAGE = 1
    IMAGE = 2
    DOCUMENT = 3
