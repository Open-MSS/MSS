# -*- coding: utf-8 -*-
"""

    mslib.mscolab.chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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

from mslib.mscolab.models import db, Message, User


class ChatManager(object):
    """Class with handler functions for chat related functionalities"""

    def __init__(self):
        pass

    def add_message(self, user, text, roomname, system_message=False):
        """
        text: message to be emitted to room and saved to db
        roomname: room-name(p_id) to which message is emitted,
        user: User object, one which emits the message
        system_message: whether the message is a save alert or normal text message
        """
        message = Message(roomname, user.id, text, system_message)
        db.session.add(message)
        db.session.commit()
        return message

    def get_messages(self, p_id, timestamp=None):
        """
        p_id: project id
        timestamp:  if provided, messages only after this time stamp is provided
        """
        if timestamp is None:
            timestamp = datetime.datetime(1970, 1, 1)
        else:
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d, %H:%M:%S")
        messages = Message.query \
            .outerjoin(User, Message.u_id == User.id) \
            .add_columns(User.username, Message.id, Message.u_id, Message.text,
                         Message.system_message, Message.created_at) \
            .filter(Message.p_id == p_id) \
            .filter(Message.created_at > timestamp) \
            .all()

        messages = list(map(lambda message: {
                            'id': message.id,
                            'u_id': message.u_id,
                            'username': message.username,
                            'text': message.text,
                            'system_message': message.system_message,
                            'time': message.created_at.strftime("%Y-%m-%d, %H:%M:%S")
                            }, messages))
        return messages

    def edit_message(self, message_id, new_message_text):
        message = Message.query.filter_by(id=message_id).first()
        message.text = new_message_text
        db.session.commit()

    def delete_message(self, message_id):
        Message.query.filter(Message.id == message_id).delete()
        db.session.commit()
