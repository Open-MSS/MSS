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
import MySQLdb as ms
import os
import sys
from flask import Flask

from mslib.mscolab.conf import SQLALCHEMY_DB_URI
from mslib.mscolab.models import User, Project, Permission
from mslib.mscolab.conf import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST

try:
    db = ms.connect(host=DB_HOST,    # your host, usually localhost
                    user=DB_USER,         # your username
                    passwd=DB_PASSWORD,  # your password
                    db=DB_NAME)        # name of the data base
    cursor = db.cursor()
    print("Database exists, please drop it before running mscolab/demodata.py")
    sys.exit(0)
except Exception as e:
    print(e)
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


from mslib.mscolab.server import db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = 'secret!'
db.init_app(app)
with app.app_context():
    data = [
        ('a', 8, ('$6$rounds=656000$cPQdxVHb1tlkDNil$Ohb.ZDN350IBuoVozgTg3cmdMKRaBQCJ1KvHPjKyGhnygd',
                  '.T6x6cyYVddWp/Hc9JFjT5cY9JNw75eTsG0kDt11'), 'a'),
        ('b', 9, ('$6$rounds=656000$DqUls/5/BfWuTReI$dJvxnZrsgeo.sKyIYBGn3ShJ',
                  '.Ccm98Q6gWcETruuWIgBWxL7RtRwmUAQ0I6b2cGITR5ksTDN2KK8xPJEm4v6c1'), 'b'),
        ('c', 10, ('$6$rounds=656000$z5PgqRSetyiQh4FE$a/1R6JSPieTp',
                   '32u4xnPY3OBremIQaHcBlmDeFqJ20WyDrd9f.EP',
                   '.i4yIB/nykv9hmKfGakLJcCaGJ/mb.2uDe1'), 'c'),
    ]
    for data_point in data:
        user = User(data_point[0], data_point[2], data_point[3])
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
        (1, 8, 1, 'admin'),
        (2, 9, 1, 'collaborator'),
        (3, 9, 2, 'admin'),
        (4, 10, 2, 'collaborator'),
        (5, 10, 3, 'admin'),
        (6, 8, 3, 'collaborator'),
        (7, 10, 1, 'viewer'),
    ]
    for data_point in data:
        project = Permission(data_point[1], data_point[2], data_point[3])
        db.session.add(project)
    db.session.commit()
    cursor.close()
