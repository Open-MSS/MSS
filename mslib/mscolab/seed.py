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
import logging
import fs
from flask import Flask
import git
from sqlalchemy.exc import IntegrityError

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import User, db, Permission, Operation


app = Flask(__name__, static_url_path='')


def add_all_users_to_all_operations(access_level='collaborator'):
    """ on db level we add all users as collaborator to all operations """
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        all_operations = Operation.query.all()
        all_path = [operation.path for operation in all_operations]
        db.session.close()
    for path in all_path:
        access_level = 'collaborator'
        if path == "TEMPLATE":
            access_level = 'admin'
        add_all_users_default_operation(path=path, access_level=access_level)


def add_all_users_default_operation(path='TEMPLATE', description="Operation to keep all users", access_level='admin'):
    """ on db level we add all users to the operation TEMPLATE for user handling"""
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        operation_available = Operation.query.filter_by(path=path).first()
        if not operation_available:
            operation = Operation(path, description)
            db.session.add(operation)
            db.session.commit()
            with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as file_dir:
                if not file_dir.exists(path):
                    file_dir.makedir(path)
                    file_dir.writetext(f'{path}/main.ftml', mscolab_settings.STUB_CODE)
                    # initiate git
                    r = git.Repo.init(fs.path.join(mscolab_settings.DATA_DIR, 'filedata', path))
                    r.git.clear_cache()
                    r.index.add(['main.ftml'])
                    r.index.commit("initial commit")

        operation = Operation.query.filter_by(path=path).first()
        op_id = operation.id
        user_list = User.query \
            .join(Permission, (User.id == Permission.u_id) & (Permission.op_id == op_id), isouter=True) \
            .add_columns(User.id, User.username) \
            .filter(Permission.u_id.is_(None))

        new_u_ids = [user.id for user in user_list]
        new_permissions = []
        for u_id in new_u_ids:
            new_permissions.append(Permission(u_id, operation.id, access_level))
        db.session.add_all(new_permissions)
        try:
            db.session.commit()
            return True
        except IntegrityError as err:
            db.session.rollback()
            logging.debug(f"Error writing to db: {err}")
        db.session.close()


def delete_user(email):
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        user = User.query.filter_by(emailid=str(email)).first()
        if user:
            logging.info(f"User: {email} deleted from db")
            db.session.delete(user)
            db.session.commit()
            db.session.close()
            return True
        db.session.close()
        return False


def add_user(email, username, password):
    """
    on db level we add a user
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    template = f"""
    "MSCOLAB_mailid": "{email}",
    "MSCOLAB_password": "{password}",
"""
    with app.app_context():
        user_email_exists = User.query.filter_by(emailid=str(email)).first()
        user_name_exists = User.query.filter_by(username=str(username)).first()
        if not user_email_exists and not user_name_exists:
            db_user = User(email, username, password)
            db.session.add(db_user)
            db.session.commit()
            db.session.close()
            logging.info(f"Userdata: {email} {username} {password}")
            logging.info(template)
            return True
        else:
            logging.info(f"{user_name_exists} already in db")
    return False


def get_user(email):
    with app.app_context():
        return User.query.filter_by(emailid=str(email)).first()


def get_operation(operation_name):
    with app.app_context():
        return Operation.query.filter_by(path=operation_name).first()


def add_operation(operation_name, description):
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        operation_available = Operation.query.filter_by(path=operation_name).first()
        if not operation_available:
            operation = Operation(operation_name, description)
            db.session.add(operation)
            db.session.commit()
            with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as file_dir:
                if not file_dir.exists(operation_name):
                    file_dir.makedir(operation_name)
                    file_dir.writetext(f'{operation_name}/main.ftml', mscolab_settings.STUB_CODE)
                    # initiate git
                    r = git.Repo.init(fs.path.join(mscolab_settings.DATA_DIR, 'filedata', operation_name))
                    r.git.clear_cache()
                    r.index.add(['main.ftml'])
                    r.index.commit("initial commit")
            return True
        else:
            return False


def delete_operation(operation_name):
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        operation = Operation.query.filter_by(path=operation_name).first()
        if operation:
            db.session.delete(operation)
            db.session.commit()
            db.session.close()
            return True
        db.session.close()
        return False


def add_user_to_operation(path=None, access_level='admin', emailid=None):
    """ on db level we add all users to the operation TEMPLATE for user handling"""
    if None in (path, emailid):
        return False
    app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        operation = Operation.query.filter_by(path=path).first()
        if operation:

            user = User.query.filter_by(emailid=emailid).first()
            if user:
                new_permissions = [Permission(user.id, operation.id, access_level)]
                db.session.add_all(new_permissions)
                try:
                    db.session.commit()
                    return True
                except IntegrityError as err:
                    db.session.rollback()
                    logging.debug(f"Error writing to db: {err}")
                db.session.close()
    return False


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

        # create operations
        operations = [{
            'id': 1,
            'path': 'one',
            'description': 'a, b',
            'category': 'default'
        }, {
            'id': 2,
            'path': 'two',
            'description': 'b, c',
            'category': 'default'
        }, {
            'id': 3,
            'path': 'three',
            'description': 'a, c',
            'category': 'default'
        }, {
            'id': 4,
            'path': 'four',
            'description': 'd',
            'category': 'default'
        }, {
            'id': 5,
            'path': 'Admin_Test',
            'description': 'Operation for testing admin window',
            'category': 'default'
        }, {
            'id': 6,
            'path': 'test_mscolab',
            'description': 'Operation for testing mscolab main window',
            'category': 'default'
        }]
        for operation in operations:
            db_operation = Operation(operation['path'], operation['description'], operation['category'])
            db_operation.id = operation['id']
            db.session.add(db_operation)

        # create permissions
        permissions = [{
            'u_id': 8,
            'op_id': 1,
            'access_level': "creator"
        }, {
            'u_id': 9,
            'op_id': 1,
            'access_level': "collaborator"
        }, {
            'u_id': 9,
            'op_id': 2,
            'access_level': "creator"
        }, {
            'u_id': 10,
            'op_id': 2,
            'access_level': "collaborator"
        }, {
            'u_id': 10,
            'op_id': 3,
            'access_level': "creator"
        }, {
            'u_id': 8,
            'op_id': 3,
            'access_level': "collaborator"
        }, {
            'u_id': 10,
            'op_id': 1,
            'access_level': "viewer"
        }, {
            'u_id': 11,
            'op_id': 4,
            'access_level': 'creator'
        }, {
            'u_id': 8,
            'op_id': 4,
            'access_level': 'admin'
        }, {
            'u_id': 13,
            'op_id': 3,
            'access_level': 'viewer'
        }, {
            'u_id': 12,
            'op_id': 5,
            'access_level': 'creator'
        }, {
            'u_id': 12,
            'op_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 15,
            'op_id': 5,
            'access_level': 'viewer'
        }, {
            'u_id': 14,
            'op_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 15,
            'op_id': 3,
            'access_level': 'collaborator'
        }, {
            'u_id': 16,
            'op_id': 6,
            'access_level': 'creator'
        }, {
            'u_id': 17,
            'op_id': 6,
            'access_level': 'admin'
        }]
        for perm in permissions:
            db_perm = Permission(perm['u_id'], perm['op_id'], perm['access_level'])
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
