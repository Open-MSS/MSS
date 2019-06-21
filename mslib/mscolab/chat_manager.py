# -*- coding: utf-8 -*-
"""

    mslib.mscolab.chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
from mslib.mscolab.models import db, Message


class ChatManager(object):
    """Class with handler functions for chat related functionalities"""

    def __init__(self):
        pass

    def add_message(self, user, text, roomname):
        """
        text: message to be emitted to room and saved to db
        roomname: room-name(p_id) to which message is emitted,
        user: User object, one which emits the message
        """
        message = Message(roomname, user.id, text)
        db.session.add(message)
        db.session.commit()
        return message

    def get_messages(self, p_id, last_timestamp=None):
        """
        p_id: project id
        last_timestamp:  if provided, messages only after this time stamp is provided
        """
        messages = Message.query.filter_by(p_id=p_id)
        if last_timestamp:
            messages = messages.filter(Message.created_at > last_timestamp)
        messages = messages.all()
        return messages
