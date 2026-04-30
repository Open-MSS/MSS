# -*- coding: utf-8 -*-
"""
    mslib.mscolab.events
    ~~~~~~~~~~~~~~~~~~~~

    This module defines all socket event names used in the mscolab module.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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


class SocketEvents:
    """Registry of all Socket.IO event names used in MSColab."""

    # Connection events
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    START = 'start'

    # Chat events
    CHAT_MESSAGE = 'chat-message'
    CHAT_MESSAGE_CLIENT = 'chat-message-client'
    CHAT_MESSAGE_REPLY_CLIENT = 'chat-message-reply-client'
    EDIT_MESSAGE = 'edit-message'
    EDIT_MESSAGE_CLIENT = 'edit-message-client'
    DELETE_MESSAGE = 'delete-message'
    DELETE_MESSAGE_CLIENT = 'delete-message-client'

    # File events
    FILE_SAVE = 'file-save'
    FILE_CHANGED = 'file-changed'

    # Permission events
    ADD_USER_TO_OPERATION = 'add-user-to-operation'
    # ToDo rename to same word order
    UPDATE_OPERATION_LIST = 'operation-list-update'
    OPERATION_SELECTED = 'operation-selected'

    # Active user events
    ACTIVE_USER_UPDATE = 'active-user-update'

    # Permission management events
    NEW_PERMISSION = 'new-permission'
    UPDATE_PERMISSION = 'update-permission'
    REVOKE_PERMISSION = 'revoke-permission'
    OPERATION_PERMISSIONS_UPDATED = 'operation-permissions-updated'

    # Operation management events
    OPERATION_DELETED = 'operation-deleted'

    @classmethod
    def get_all_events(cls):
        """Return a set of all event names."""
        return {
            getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and isinstance(getattr(cls, attr), str)
        }
