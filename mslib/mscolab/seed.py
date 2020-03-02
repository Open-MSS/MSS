# -*- coding: utf-8 -*-
"""

    mslib.mscolab.seed
    ~~~~~~~~~~~~~~~~~~~~

    Seeder utility for database

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
from flask import Flask

from mslib.mscolab.models import User, db, Permission, Project
from mslib.mscolab.conf import mscolab_settings
# set the project root directory as the static folder
app = Flask(__name__, static_url_path='')


def seed_data(db_uri):

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY
    db.init_app(app)

    with app.app_context():
        # create users
        users = [{
            'username': 'a',
            'id': 8,
            'password': 'a',
            'emailid': 'a'
        }, {
            'username': 'b',
            'id': 9,
            'password': 'b',
            'emailid': 'b'
        }, {
            'username': 'c',
            'id': 10,
            'password': 'c',
            'emailid': 'c'
        }]
        for user in users:
            db_user = User(user['emailid'], user['username'], user['password'])
            db_user.id = user['id']
            db.session.add(db_user)
        db.session.commit()

        # create projects
        projects = [{
            'id': 1,
            'path': 'one',
            'description': 'a, b',
            'autosave': False
        }, {
            'id': 2,
            'path': 'two',
            'description': 'b, c',
            'autosave': False
        }, {
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
        }, {
            'u_id': 9,
            'p_id': 1,
            'access_level': "collaborator"
        }, {
            'u_id': 9,
            'p_id': 2,
            'access_level': "creator"
        }, {
            'u_id': 10,
            'p_id': 2,
            'access_level': "collaborator"
        }, {
            'u_id': 10,
            'p_id': 3,
            'access_level': "creator"
        }, {
            'u_id': 8,
            'p_id': 3,
            'access_level': "collaborator"
        }, {
            'u_id': 10,
            'p_id': 1,
            'access_level': "viewer"
        }]
        for perm in permissions:
            db_perm = Permission(perm['u_id'], perm['p_id'], perm['access_level'])
            db.session.add(db_perm)
        db.session.commit()
        db.session.close()


def create_tables(db_uri):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY
    db.init_app(app)
    with app.app_context():
        db.create_all()
