# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility functions for mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.

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
import fs
import os
import logging

from mslib.mscolab.conf import mscolab_settings


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


def get_message_dict(message):
    return {
        "id": message.id,
        "u_id": message.u_id,
        "username": message.user.username,
        "text": message.text,
        "message_type": message.message_type,
        "reply_id": message.reply_id,
        "replies": [],
        "time": message.created_at.strftime("%Y-%m-%d, %H:%M:%S")
    }


def os_fs_create_dir(dir):
    if '://' in dir:
        try:
            _ = fs.open_fs(dir)
        except fs.errors.CreateFailed:
            logging.error('Make sure that the FS url "%s" exists' % dir)
        except fs.opener.errors.UnsupportedProtocol:
            logging.error(f'FS url "{dir}" not supported')
    else:
        _dir = os.path.expanduser(dir)
        if not os.path.exists(_dir):
            os.makedirs(_dir)


def create_files():
    os_fs_create_dir(mscolab_settings.MSCOLAB_DATA_DIR)
    os_fs_create_dir(mscolab_settings.UPLOAD_FOLDER)
