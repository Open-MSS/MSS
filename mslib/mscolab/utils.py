# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility functions for mscolab

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.

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
import os
import re
from pathlib import Path

# Operation names become directory names below OPERATIONS_DATA. The msui client
# applies the same rule before sending a new operation.
OPERATION_PATH_PATTERN = re.compile(r"[a-zA-Z0-9_-]+")

# URL namespace under which chat attachments are served by the chat blueprint.
# This is deliberately independent of the directory name configured as
# UPLOAD_FOLDER, which may be named arbitrarily.
ATTACHMENTS_URL_PREFIX = "uploads"


def get_recent_op_id(fm, user):
    operations = fm.list_operations(user)
    op_id = None
    if operations:
        op_id = operations[-1]["op_id"]
    return op_id


def get_session_id(sockets, u_id):
    s_id = None
    for ss in sockets:
        if ss["u_id"] == u_id:
            s_id = ss["s_id"]
    return s_id


def get_user_id(sockets, s_id):
    u_id = None
    for ss in sockets:
        if ss["s_id"] == s_id:
            u_id = ss["u_id"]
    return u_id


def get_message_dict(message):
    return {
        "id": message.id,
        "u_id": message.u_id,
        "username": message.user.username,
        "text": message.text,
        "message_type": message.message_type,
        "reply_id": message.reply_id,
        "replies": [],
        "time": message.created_at.isoformat()
    }


def is_valid_operation_path(path):
    """True if path is usable as an operation name, i.e. as a single directory name"""
    return isinstance(path, str) and OPERATION_PATH_PATTERN.fullmatch(path) is not None


def get_operation_dir(data_dir, path):
    """
    Return the directory of the operation named path below data_dir.

    Raises ValueError if that directory would not be a direct child of data_dir,
    e.g. for names like "", "." or ".." stored before names were validated.
    """
    # normalised lexically, so that symlinked operation directories keep working
    data_dir = Path(os.path.abspath(data_dir))
    operation_dir = Path(os.path.normpath(data_dir / path))
    if not path or operation_dir.parent != data_dir:
        raise ValueError(f"operation path {path!r} is outside of {data_dir}")
    return operation_dir
