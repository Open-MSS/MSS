# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat functionalities

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
import socketio
import requests
import subprocess
import json
import logging
import os
from flask import Flask
import datetime

from mslib.mscolab.conf import SQLALCHEMY_DB_URI
from mslib.mscolab.models import db
from mslib.mscolab.sockets_manager import fm
from mslib._tests.constants import MSCOLAB_URL_TEST


class Test_Sockets(object):

    def setup(self):
        self.sockets = []
        cwd = os.getcwd()
        path_to_server = cwd + "/mslib/mscolab/server.py"
        self.proc = subprocess.Popen(["python", path_to_server], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        try:
            outs, errs = self.proc.communicate(timeout=4)
        except Exception as e:
            logging.debug("Server isn't running")
            logging.debug(e)
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        db.init_app(self.app)

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
            self.proc.kill()
