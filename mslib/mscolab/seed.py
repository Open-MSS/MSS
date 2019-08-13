# -*- coding: utf-8 -*-
"""

    mslib.mscolab.seed
    ~~~~~~~~~~~~~~~~~~~~

    Seeder utility for database

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

from flask import Flask, request, g
import logging
import json
import datetime
import functools
from validate_email import validate_email

from mslib.mscolab.models import User, db, Permission, Project
from mslib.mscolab.conf import SQLALCHEMY_DB_URI, SECRET_KEY
from mslib.mscolab.sockets_manager import socketio as sockio, cm, fm
# set the project root directory as the static folder
app = Flask(__name__, static_url_path='')
# sockio.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)

def seed_data():
    with app.app_context():
        # create users
        users = [{
            'username': 'a',
            'id': 8,
            'password': '$6$rounds=656000$cPQdxVHb1tlkDNil$Ohb.ZDN350IBuoVozgTg3cmdMKRaBQCJ1KvHPjKyGhnygd.T6x6cyYVddWp/Hc9JFjT5cY9JNw75eTsG0kDt11',
            'emailid': 'a'
        },{
            'username': 'b',
            'id': 9,
            'password': '$6$rounds=656000$DqUls/5/BfWuTReI$dJvxnZrsgeo.sKyIYBGn3ShJ.Ccm98Q6gWcETruuWIgBWxL7RtRwmUAQ0I6b2cGITR5ksTDN2KK8xPJEm4v6c1',
            'emailid': 'b'
        },{
            'username': 'c',
            'id': 10,
            'password': '$6$rounds=656000$z5PgqRSetyiQh4FE$a/1R6JSPieTp32u4xnPY3OBremIQaHcBlmDeFqJ20WyDrd9f.EP.i4yIB/nykv9hmKfGakLJcCaGJ/mb.2uDe1',
            'emailid': 'c'
        }]
        for user in users:
            db_user = User(user['username'], user['password'], user['emailid'])
            db_user.id = user['id']
            db.session.add(db_user)
        db.session.commit()

        # create projects
        projects = [{
            'id': 1,
            'path': 'one',
            'description': 'a, b',
            'autosave': False
        },{
            'id': 2,
            'path': 'two',
            'description': 'b, c',
            'autosave': False
        },{
            'id': 3,
            'path': 'three`',
            'description': 'a, c',
            'autosave': False
        }]
        for project in projects:
            db_project = Project(project['path'], project['description'], project['autosave'])
            db_project.id = project['id']
            db.session.add(db_project)
        db.session.commit()

        # create permissions
        permissions = [{
            'u_id': 8,
            'p_id': 1,
            'access_level': "creator"
        },{
            'u_id': 9,
            'p_id': 1,
            'access_level': "collaborator"
        },{
            'u_id': 9,
            'p_id': 2,
            'access_level': "creator"
        },{
            'u_id': 10,
            'p_id': 2,
            'access_level': "collaborator"
        },{
            'u_id': 10,
            'p_id': 3,
            'access_level': "creator"
        },{
            'u_id': 8,
            'p_id': 3,
            'access_level': "collaborator"
        },{
            'u_id': 10,
            'p_id': 1,
            'access_level': "viewer"
        }]
        for perm in permissions:
            db_perm = Permission(perm['u_id'], perm['p_id'], perm['access_level'])
            db.session.add(db_perm)
        db.session.commit()


def create_tables():
    with app.app_context():
        db.create_all()    
