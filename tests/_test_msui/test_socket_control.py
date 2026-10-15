# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_socket_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the requests msui sends to the MSColab server.

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
import mock
import requests

from mslib.mscolab.api.schemas import TOKEN_HEADER
from mslib.msui.socket_control import mscolab_get


def _prepared_request(*args, **kwargs):
    with mock.patch("mslib.msui.socket_control.requests.get") as get:
        mscolab_get(*args, **kwargs)
    (url,), sent = get.call_args
    sent.pop("timeout")
    return requests.Request("GET", url, **sent).prepare()


def test_mscolab_get_parameters_in_query_string_token_in_header():
    request = _prepared_request("http://localhost:8083/operations", "secret-token", {"skip_archived": "True"})
    assert request.url == "http://localhost:8083/operations?skip_archived=True"
    assert request.headers[TOKEN_HEADER] == "secret-token"
    assert "secret-token" not in request.url


def test_mscolab_get_body_for_servers_up_to_11():
    # they read the token, and user_id of fetch_profile_image, only from the query string or the body
    request = _prepared_request("http://localhost:8083/fetch_profile_image", "secret-token", {"user_id": 1})
    assert request.url == "http://localhost:8083/fetch_profile_image?user_id=1"
    assert request.body == "user_id=1&token=secret-token"
