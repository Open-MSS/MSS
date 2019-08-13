# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab/utils

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi

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

from mslib.mscolab.server import db, app, initialize_managers, start_server
from mslib.mscolab.models import User
from mslib.mscolab.utils import get_recent_pid
from mslib._tests.constants import TEST_SQLALCHEMY_DB_URI, TEST_MSCOLAB_DATA_DIR

import multiprocessing
import time


class Test_Utils(object):
    def setup(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = TEST_SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = TEST_MSCOLAB_DATA_DIR
        self.app, sockio, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        self.p = multiprocessing.Process(
            target=start_server,
            args=(self.app, sockio, cm, fm,),
            kwargs={'port': 8084})
        self.p.start()
        db.init_app(self.app)
        time.sleep(1)
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def test_get_recent_pid(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        assert p_id == 3

    def teardown(self):
        self.p.terminate()
        pass
