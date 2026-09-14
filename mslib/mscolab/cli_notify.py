# -*- coding: utf-8 -*-
"""

    mslib.mscolab.cli_notify
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Lets mscolab CLI actions (see mslib.mscolab.seed) tell an already-running
    mscolab server to emit a socket.io event on their behalf. The CLI mutates
    the database directly, in its own short-lived process, so it has no access
    to the server's live socket connections and would otherwise leave connected
    clients (e.g. the "Manage Users" dialog in msui) unaware of the change.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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

import logging

import requests

from mslib.mscolab.app import APP


def notify_socket_event(event, **payload):
    """
    Best-effort notification to the running mscolab server's internal admin
    endpoint. Silently logs and gives up if the server isn't reachable (e.g. the
    CLI is used for an initial `db --seed` before any server has been started) -
    there are no connected clients to notify in that case anyway.
    """
    url = APP.config['SERVER_URL'].rstrip('/') + '/internal_notify'
    data = {"event": event, "token": APP.config['ADMIN_TOKEN'], **payload}
    try:
        response = requests.post(url, data=data, timeout=2)
        if not response.ok:
            logging.debug("mscolab server rejected notify for %s: %s", event, response.text)
    except requests.exceptions.RequestException as ex:
        logging.debug("Could not notify mscolab server of %s (server may not be running): %s", event, ex)
