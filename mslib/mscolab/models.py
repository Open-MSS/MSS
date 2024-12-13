# -*- coding: utf-8 -*-
"""

    mslib.mscolab.models
    ~~~~~~~~~~~~~~~~~~~~

    sqlalchemy models for mscolab database

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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

import datetime
import logging
import jwt

from passlib.apps import custom_app_context as pwd_context
import sqlalchemy.types

from mslib.mscolab.app import db
from mslib.mscolab.message_type import MessageType


class AwareDateTime(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.astimezone(datetime.timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # noqa: A003
    username = db.Column(db.String(255))
    emailid = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    profile_image_path = db.Column(db.String(255), nullable=True)  # relative path
    registered_on = db.Column(AwareDateTime, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(AwareDateTime, nullable=True)
    permissions = db.relationship('Permission', cascade='all,delete,delete-orphan', backref='user')
    authentication_backend = db.Column(db.String(255), nullable=False, default='local')
    fullname = db.Column(db.String(255), nullable=True)

    def __init__(self, emailid, username, password, profile_image_path=None, confirmed=False,
                 confirmed_on=None, authentication_backend='local', fullname=""):
        self.username = str(username)
        self.emailid = str(emailid)
        self.hash_password(password)
        self.profile_image_path = profile_image_path
        self.registered_on = datetime.datetime.now(tz=datetime.timezone.utc)
        self.confirmed = bool(confirmed)
        self.confirmed_on = confirmed_on
        self.authentication_backend = str(authentication_backend)
        self.fullname = str(fullname)

    def __repr__(self):
        return f'<User {self.username}>'

    def hash_password(self, password):
        self.password = pwd_context.hash(password)

    def verify_password(self, password_):
        return pwd_context.verify(password_, self.password)

    def generate_auth_token(self, expiration=None):
        # Importing conf here to avoid loading settings on opening chat window
        from mslib.mscolab.conf import mscolab_settings
        expiration = mscolab_settings.__dict__.get('EXPIRATION', expiration)
        if expiration is None:
            expiration = 864000
            token = jwt.encode(
                {
                    "id": self.id,
                    "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=expiration)
                },
                mscolab_settings.SECRET_KEY,
                algorithm="HS256"
            )
            return token

    @staticmethod
    def verify_auth_token(token):
        """
        token is the authentication string provided by client for each request
        """
        # Importing conf here to avoid loading settings on opening chat window
        from mslib.mscolab.conf import mscolab_settings
        try:
            data = jwt.decode(
                token,
                mscolab_settings.SECRET_KEY,
                leeway=datetime.timedelta(seconds=30),
                algorithms=["HS256"]
            )
        except Exception as e:
            logging.debug("Bad Token %s", str(e))
            return None

        user = User.query.filter_by(id=data.get('id')).first()
        return user


class Permission(db.Model):

    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # noqa: A003
    op_id = db.Column(db.Integer, db.ForeignKey('operations.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    access_level = db.Column(db.Enum("admin", "collaborator", "viewer", "creator", name="access_level"))

    def __init__(self, u_id, op_id, access_level):
        """
        u_id: user-id
        op_id: process-id
        access_level: the type of authorization to the operation
        """
        self.u_id = int(u_id)
        self.op_id = int(op_id)
        self.access_level = str(access_level)

    def __repr__(self):
        return f'<Permission u_id: {self.u_id}, op_id:{self.op_id}, access_level: {str(self.access_level)}>'


class Operation(db.Model):

    __tablename__ = "operations"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # noqa: A003
    path = db.Column(db.String(255), unique=True)
    category = db.Column(db.String(255))
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    last_used = db.Column(AwareDateTime)

    def __init__(self, path, description, last_used=None, category="default", active=True):
        """
        path: path to the operation
        description: small description of operation
        category: name of category
        """
        self.path = str(path)
        self.description = str(description)
        self.category = str(category)
        self.active = bool(active)
        if self.last_used is None:
            self.last_used = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            self.last_used = last_used

    def __repr__(self):
        return f'<Operation path: {self.path}, desc: {self.description},' \
               f' cat: {self.category}, active: {self.active}, ' \
               f'last_used: {self.last_used}> '


class Message(db.Model):

    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # noqa: A003
    op_id = db.Column(db.Integer, db.ForeignKey('operations.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    text = db.Column(db.Text)
    message_type = db.Column(db.Enum(MessageType), default=MessageType.TEXT)
    reply_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    created_at = db.Column(AwareDateTime, default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    user = db.relationship('User')
    replies = db.relationship('Message', cascade='all,delete,delete-orphan', single_parent=True)

    def __init__(self, op_id, u_id, text, message_type=MessageType.TEXT, reply_id=None):
        self.op_id = int(op_id)
        self.u_id = int(u_id)
        self.text = str(text)
        self.message_type = message_type
        self.reply_id = reply_id

    def __repr__(self):
        return f'<Message text: {self.text}, u_id: {self.u_id}, op_id: {self.op_id}>, message_type: {self.message_type}'


class Change(db.Model):

    __tablename__ = "changes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # noqa: A003
    op_id = db.Column(db.Integer, db.ForeignKey('operations.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    commit_hash = db.Column(db.String(255), default=None)
    version_name = db.Column(db.String(255), default=None)
    comment = db.Column(db.String(255), default=None)
    created_at = db.Column(AwareDateTime, default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    user = db.relationship('User')

    def __init__(self, op_id, u_id, commit_hash, version_name=None, comment=None):
        self.op_id = int(op_id)
        self.u_id = int(u_id)
        self.commit_hash = str(commit_hash)
        if version_name is not None:
            self.version_name = str(version_name)
        if comment is not None:
            self.comment = str(comment)
