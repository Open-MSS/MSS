# -*- coding: utf-8 -*-
"""

    mslib.mscolab.chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

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
import datetime
import os
import time

import fs
from werkzeug.utils import secure_filename

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, Message, MessageType
from mslib.mscolab.utils import get_message_dict


class ChatManager:
    """Class with handler functions for chat related functionalities"""

    def __init__(self):
        pass

    def add_message(self, user, text, operation_name, message_type=MessageType.TEXT, reply_id=None):
        """
        text: message to be emitted to operation and saved to db
        operation_name: operation-name(op_id) to which message is emitted,
        user: User object, one which emits the message
        message_type: Enum of type MessageType. values: TEXT, SYSTEM_MESSAGE, IMAGE, DOCUMENT
        """
        if reply_id == -1:
            reply_id = None
        message = Message(operation_name, user.id, text, message_type, reply_id)
        db.session.add(message)
        db.session.commit()
        return message

    def get_messages(self, op_id, timestamp=None):
        """
        op_id: operation id
        timestamp:  if provided, messages only after this time stamp is provided
        """
        if timestamp is None:
            timestamp = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        else:
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d, %H:%M:%S.%f %z")
        messages = Message.query \
            .filter(Message.op_id == op_id) \
            .filter(Message.reply_id.is_(None)) \
            .filter(Message.created_at > timestamp) \
            .all()

        message_list = []
        for message in messages:
            replies_list = []
            for reply in message.replies:
                reply_dict = get_message_dict(reply)
                replies_list.append(reply_dict)
            message_dict = get_message_dict(message)
            message_dict["replies"] = replies_list
            message_list.append(message_dict)

        return message_list

    def edit_message(self, message_id, new_message_text):
        message = Message.query.filter_by(id=message_id).first()
        message.text = new_message_text
        db.session.commit()

    def delete_message(self, message_id):
        message = Message.query.filter(Message.id == message_id).first()
        if message.message_type == MessageType.IMAGE or message.message_type == MessageType.DOCUMENT:
            file_name = fs.path.basename(message.text)
            with fs.open_fs(mscolab_settings.UPLOAD_FOLDER) as upload_dir:
                upload_dir.remove(fs.path.join(str(message.op_id), file_name))
        db.session.delete(message)
        db.session.commit()

    def add_attachment(self, op_id, upload_folder, file, file_token):
        with fs.open_fs('/') as home_fs:
            file_dir = fs.path.join(upload_folder, str(op_id))
            if '\\' not in file_dir:
                if not home_fs.exists(file_dir):
                    home_fs.makedirs(file_dir)
            else:
                file_dir = file_dir.replace('\\', '/')
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
            file_name, file_ext = file.filename.rsplit('.', 1)
            file_name = f'{file_name}-{time.strftime("%Y%m%dT%H%M%S")}-{file_token}.{file_ext}'
            file_name = secure_filename(file_name)
            file_path = fs.path.join(file_dir, file_name)
            file.save(file_path)
            static_dir = fs.path.basename(upload_folder)
            static_dir = static_dir.replace('\\', '/')
            static_file_path = os.path.join(static_dir, str(op_id), file_name)
        if os.path.exists(file_path):
            return static_file_path
