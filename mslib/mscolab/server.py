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
def test_authorized():
    token = request.args['token']
    user = User.verify_auth_token(token)
    if user:
        return("True")
    else:
        return("False")


@app.route("/register", methods=["POST"])
def user_register():
    email = request.args['email']
    password = request.args['password']
    screenname = request.args['screenname']
    user = User(email, screenname, password)
    db.session.add(user)
    db.session.commit()
    return('done')


def test_check_login():
    email = request.args['email']
    password = request.args['password']
    return check_login(email, password)


@socketio.on('connect')
def handle_connect():
    print("connected")
    print(request.sid)


@socketio.on('start_event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    socket_storage = {
        'id': request.sid,
        'emailid': json['emailid']
    }
    sockets.append(socket_storage)
    print(sockets)


@socketio.on('disconnect')
def handle_disconnect():
    print("disconnected")
    print(request.sid)
    # remove socket from socket_storage
    sockets[:] = [d for d in sockets if d['id'] != request.sid]
    print(sockets, request.sid)


if __name__ == '__main__':
    socketio.run(app)
