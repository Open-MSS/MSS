# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

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

from flask import Flask, request, jsonify
from flask_socketio import SocketIO

from models import User, db
from conf import SQLALCHEMY_DB_URI

app = Flask(__name__)

socketio = SocketIO(app)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = 'secret!'
db.init_app(app)

sockets = []


@app.route("/")
def hello():
    return("Testing mscolab server")


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return(user)
    return(False)


@app.route('/token')
def get_auth_token():
    email = request.args['email']
    password = request.args['password']
    user = check_login(email, password)
    if user:
        token = user.generate_auth_token()
        return(jsonify({'token': token.decode('ascii')}))
    else:
        return("False")


@app.route('/test_authorized')
def authorized():
    token = request.args['token']
    user = User.verify_auth_token(token)
    if user:
        return("True")
    else:
        return("False")


def register_user(email, password, username):
    user = User(email, username, password)
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return('False')
    db.session.add(user)
    db.session.commit()
    return('True')


@app.route("/register", methods=["POST"])
def user_register_handler():
    email = request.args['email']
    password = request.args['password']
    username = request.args['username']
    return(register_user(email, password, username))


def check_login_test():
    email = request.args['email']
    password = request.args['password']
    return check_login(email, password)


@socketio.on('connect')
def handle_connect():
    logging.info(request.sid)


@socketio.on('start_event')
def handle_my_custom_event(json):
    logging.info('received json: ' + str(json))
    socket_storage = {
        'id': request.sid,
        'emailid': json['emailid']
    }
    sockets.append(socket_storage)


@socketio.on('disconnect')
def handle_disconnect():
    logging.info("disconnected")
    logging.info(request.sid)
    # remove socket from socket_storage
    sockets[:] = [d for d in sockets if d['id'] != request.sid]


if __name__ == '__main__':
    socketio.run(app)
