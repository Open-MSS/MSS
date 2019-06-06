# -*- coding: utf-8 -*-
"""

    mslib.mscolab.models
    ~~~~~~~~~~~~~~~~~~~~

    sqlalchemy models for mscolab database

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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

from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from conf import SECRET_KEY
db = SQLAlchemy()


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    emailid = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), unique=True)

    def __init__(self, emailid, username, password):
        self.username = username
        self.emailid = emailid
        self.hash_password(password)

    def __repr__(self):
        return('<User %r>' % self.username)

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password_):
        return pwd_context.verify(password_, self.password)

    def generate_auth_token(self, expiration=600):
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired as e:
            logging.debug("Signature Expired")
            return None  # valid token, but expired
        except BadSignature as e:
            logging.debug("Bad Signature")
            return None  # invalid token
        user = User.query.filter_by(id=data['id']).first()
        return user


class Connection(db.Model):

    __tablename__ = 'connections'
    id = db.Column(db.Integer, primary_key=True)
    s_id = db.Column(db.String(255), unique=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, u_id, s_id):
        self.u_id = u_id
        self.s_id = s_id

    def __repr__(self):
        return('<Connection %s %s>'.format(self.s_id, self.u_id))
