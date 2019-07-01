#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    mslib.mscolab.demodata
    ~~~~~~~~~~~~~~~~~~~~~~

    dummydata for mscolab

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

import os
import fs
import sys
from flask import Flask
import logging
try:
    import MySQLdb as ms
except ImportError:
    ms = None
from mslib.mscolab.conf import SQLALCHEMY_DB_URI
from mslib.mscolab.models import User, Project, Permission
from mslib.mscolab.conf import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DATA_DIR, BASE_DIR


def create_data():
    if SQLALCHEMY_DB_URI.split(':')[0] == "mysql":
        if ms is None:
            logging.info("""can't complete demodata setup,
                         use sqlite3 or configure mysql with proper modules""")
            sys.exit(0)
        try:
            db = ms.connect(host=DB_HOST,    # your host, usually localhost
                            user=DB_USER,         # your username
                            passwd=DB_PASSWORD,  # your password
                            db=DB_NAME)        # name of the data base
            cursor = db.cursor()
            logging.info("Database exists, please drop it before running mscolab/demodata.py")
            sys.exit(0)
        except Exception as e:
            logging.debug(e)
            db = ms.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD)
            cursor = db.cursor()
            sql = 'CREATE DATABASE ' + DB_NAME + ';'
            cursor.execute(sql)
            db = ms.connect(host=DB_HOST,    # your host, usually localhost
                            user=DB_USER,         # your username
                            passwd=DB_PASSWORD,  # your password
                            db=DB_NAME)        # name of the data base
            cursor = db.cursor()

        PATH_TO_FILE = os.getcwd() + '/schema_seed.sql'
        for line in open(PATH_TO_FILE):
            if line.split(' ')[0] not in ['CREATE', 'SET']:
                continue
            cursor.execute(line)

        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        from mslib.mscolab.models import db
        app.config['SECRET_KEY'] = 'secret!'.encode('utf-8')
        db.init_app(app)
        with app.app_context():
            db.create_all()
            data = [
                ('a', 8, 'a', 'a'),
                ('b', 9, 'b', 'b'),
                ('c', 10, 'c', 'c'),
            ]
            for data_point in data:
                user = User(data_point[0], data_point[3], data_point[2])
                user.id = data_point[1]
                db.session.add(user)
                db.session.commit()

            data = [
                (1, 'one', 'a, b'),
                (2, 'two', 'b, c'),
                (3, 'three', 'a, c'),
            ]
            for data_point in data:
                project = Project(data_point[1], data_point[2])
                project.id = data_point[0]
                db.session.add(project)
            db.session.commit()

            data = [
                (1, 8, 1, 'creator'),
                (2, 9, 1, 'collaborator'),
                (3, 9, 2, 'creator'),
                (4, 10, 2, 'collaborator'),
                (5, 10, 3, 'creator'),
                (6, 8, 3, 'collaborator'),
                (7, 10, 1, 'viewer'),
            ]
            for data_point in data:
                project = Permission(data_point[1], data_point[2], data_point[3])
                db.session.add(project)
            db.session.commit()

        pass
    elif SQLALCHEMY_DB_URI.split(':')[0] == "sqlite":
        # path_prepend = os.path.dirname(os.path.abspath(__file__))
        fs_datadir = fs.open_fs(BASE_DIR)
        if not fs_datadir.exists('colabdata'):
            fs_datadir.makedir('colabdata')
        fs_datadir = fs.open_fs(DATA_DIR)
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        mss_dir = fs.open_fs(fs.path.combine(cur_dir, '../../docs/samples/config/mscolab/'))
        if fs_datadir.exists('mscolab.db'):
            logging.info("Database exists")
        else:
            if not fs_datadir.exists('filedata'):
                fs_datadir.makedir('filedata')
            fs.copy.copy_file(mss_dir, 'mscolab.db.sample', fs_datadir, 'mscolab.db')

    else:
        pass


if __name__ == '__main__':
    create_data()
