# -*- coding: utf-8 -*-
"""

    mslib.mscolab.models
    ~~~~~~~~~~~~~~~~~~~~

    sqlalchemy models for mscolab database

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

import datetime
import enum
import logging

from flask_sqlalchemy import SQLAlchemy
from itsdangerous import (BadSignature, SignatureExpired, TimedJSONWebSignatureSerializer as Serializer)
from passlib.apps import custom_app_context as pwd_context

from mslib.mscolab.conf import mscolab_settings

db = SQLAlchemy()


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255))
    emailid = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), unique=True)
    permissions = db.relationship('Permission', cascade='all,delete,delete-orphan', backref='user')

    def __init__(self, emailid, username, password):
        self.username = username
        self.emailid = emailid
        self.hash_password(password)

    def __repr__(self):
        return f'<User {self.username}>'

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password_):
        return pwd_context.verify(password_, self.password)

    def generate_auth_token(self, expiration=864000):
        s = Serializer(mscolab_settings.SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        """
        token is the authentication string provided by client for each request
        """
        s = Serializer(mscolab_settings.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            logging.debug("Signature Expired")
            return None  # valid token, but expired
        except BadSignature:
            logging.debug("Bad Signature")
            return None  # invalid token
        user = User.query.filter_by(id=data['id']).first()
        return user


class Connection(db.Model):

    __tablename__ = 'connections'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    s_id = db.Column(db.String(255), unique=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, u_id, s_id):
        self.u_id = u_id
        self.s_id = s_id

    def __repr__(self):
        return f'<Connection s_id: {self.s_id}, u_id: {self.u_id}>'


class Permission(db.Model):

    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    access_level = db.Column(db.Enum("admin", "collaborator", "viewer", "creator", name="access_level"))

    def __init__(self, u_id, p_id, access_level):
        """
        u_id: user-id
        p_id: process-id
        access_level: the type of authorization to the project
        """
        self.u_id = u_id
        self.p_id = p_id
        self.access_level = access_level

    def __repr__(self):
        return f'<Permission u_id: {self.u_id}, p_id:{self.p_id}, access_level: {str(self.access_level)}>'


class Project(db.Model):

    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    path = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))
    autosave = db.Column(db.Boolean)

    def __init__(self, path, description, autosave):
        """
        path: path to the project
        description: small description of project,
        autosave: a boolean to show if autosave is enabled or disabled
            for the project
        """
        self.path = path
        self.description = description
        self.autosave = autosave

    def __repr__(self):
        return f'<Project path: {self.path}, desc: {self.description}>'


class MessageType(enum.IntEnum):
    TEXT = 0
    SYSTEM_MESSAGE = 1
    IMAGE = 2
    DOCUMENT = 3


class Message(db.Model):

    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    text = db.Column(db.Text)
    message_type = db.Column(db.Enum(MessageType), default=MessageType.TEXT)
    reply_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('User')
    replies = db.relationship('Message', cascade='all,delete,delete-orphan', single_parent=True)

    def __init__(self, p_id, u_id, text, message_type=MessageType.TEXT, reply_id=None):
        self.p_id = p_id
        self.u_id = u_id
        self.text = text
        self.message_type = message_type
        self.reply_id = reply_id

    def __repr__(self):
        return f'<Message text: {self.text}, u_id: {self.u_id}, p_id: {self.p_id}>, message_type: {self.message_type}'


class Change(db.Model):

    __tablename__ = "changes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.TEXT)
    comment = db.Column(db.String(255), default=None)
    commit_hash = db.Column(db.String(255), default=None)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, p_id, u_id, content, commit_hash, comment=""):
        self.p_id = p_id
        self.u_id = u_id
        self.content = content
        self.commit_hash = commit_hash
        self.comment = comment
