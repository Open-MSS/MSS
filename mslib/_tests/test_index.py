# -*- coding: utf-8 -*-
"""

    mslib.test_index
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests index

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
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

from mslib import index


def test_xstatic():
    assert index._xstatic('jquery') is not None
    assert index._xstatic('bootstrap') is not None
    assert index._xstatic('notinstalled') is None


def test_app_loader():
    assert index.DOCS_SERVER_PATH.endswith('mslib')
    app = index.app_loader("example")
    assert app is not None
    with app.test_client() as c:
        response = c.get('/xstatic/bootstrap/css/bootstrap.css')
        assert response.status_code == 200
        response = c.get('mss_theme/img/wise12_overview.png')
        assert response.status_code == 200
        response = c.get('/index')
        assert response.status_code == 200
        response = c.get('/mss')
        assert response.status_code == 200
        response = c.get('/mss/install')
        assert response.status_code == 200
        response = c.get('/mss/help')
        assert response.status_code == 200
        response = c.get('/mss/favicon.ico')
        assert response.status_code == 200
        response = c.get('/mss/logo.png')
        assert response.status_code == 200
