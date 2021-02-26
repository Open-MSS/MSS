# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab/utils

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.

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
import pytest
from mslib.mscolab.server import db, APP, initialize_managers
from mslib.mscolab.models import User
from mslib.mscolab.utils import get_recent_pid
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.mscolab import handle_db_seed


@pytest.mark.usefixtures("start_mscolab_server")
@pytest.mark.usefixtures("stop_server")
@pytest.mark.usefixtures("create_data")
class Test_Utils(object):
    def setup(self):
        handle_db_seed()
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def test_get_recent_pid(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        assert p_id == 4
