# -*- coding: utf-8 -*-
"""

    mslib.mscolab.seed
    ~~~~~~~~~~~~~~~~~~~~

    Seeder utility for database

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
import fs
from flask import Flask
import git

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import User, db, Permission, Project

app = Flask(__name__, static_url_path='')


def seed_data():
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
        }, {
            'username': 'd',
            'id': 11,
            'password': 'd',
            'emailid': 'd'
        }, {
            'username': 'test1',
            'id': 12,
            'password': 'test1',
            'emailid': 'test1'
        }, {
            'username': 'test2',
            'id': 13,
            'password': 'test2',
            'emailid': 'test2'
        }, {
            'username': 'test3',
            'id': 14,
            'password': 'test3',
            'emailid': 'test3'
        }, {
            'username': 'test4',
            'id': 15,
            'password': 'test4',
            'emailid': 'test4'
        }, {
            'username': 'mscolab_user',
            'id': 16,
            'password': 'password',
            'emailid': 'mscolab_user'
        }, {
            'username': 'merge_waypoints_user',
            'id': 17,
            'password': 'password',
            'emailid': 'merge_waypoints_user'
        }]
        for user in users:
            db_user = User(user['emailid'], user['username'], user['password'])
            db_user.id = user['id']
            db.session.add(db_user)

        # create projects
        projects = [{
            'id': 1,
            'path': 'one',
            'description': 'a, b'
        }, {
            'id': 2,
            'path': 'two',
            'description': 'b, c'
        }, {
            'id': 3,
            'path': 'three',
            'description': 'a, c'
        }, {
            'id': 4,
            'path': 'four',
            'description': 'd'
        }, {
            'id': 5,
            'path': 'Admin_Test',
            'description': 'Project for testing admin window'
        }, {
            'id': 6,
            'path': 'test_mscolab',
            'description': 'Project for testing mscolab main window'
        }]
        for project in projects:
            db_project = Project(project['path'], project['description'])
            db_project.id = project['id']
            db.session.add(db_project)

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
        }, {
            'u_id': 11,
            'p_id': 4,
            'access_level': 'creator'
        }, {
            'u_id': 8,
            'p_id': 4,
            'access_level': 'admin'
        }, {
            'u_id': 13,
            'p_id': 3,
            'access_level': 'viewer'
        }, {
            'u_id': 12,
            'p_id': 5,
            'access_level': 'creator'
        }, {
            'u_id': 12,
            'p_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 15,
            'p_id': 5,
            'access_level': 'viewer'
        }, {
            'u_id': 14,
            'p_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 15,
            'p_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 16,
            'p_id': 6,
            'access_level': 'creator'
        }, {
            'u_id': 17,
            'p_id': 6,
            'access_level': 'admin'
        }]
        for perm in permissions:
            db_perm = Permission(perm['u_id'], perm['p_id'], perm['access_level'])
            db.session.add(db_perm)
        db.session.commit()
        db.session.close()

    with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as file_dir:
        file_paths = ['one', 'two', 'three', 'four', 'Admin_Test', 'test_mscolab']
        for file_path in file_paths:
            file_dir.makedir(file_path)
            file_dir.writetext(f'{file_path}/main.ftml', mscolab_settings.STUB_CODE)
            # initiate git
            r = git.Repo.init(fs.path.join(mscolab_settings.DATA_DIR, 'filedata', file_path))
            r.git.clear_cache()
            r.index.add(['main.ftml'])
            r.index.commit("initial commit")
