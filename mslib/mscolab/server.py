from flask import Flask, request
from flask_socketio import SocketIO
from models import User, Connection, db
import sys


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

@app.route("/register", methods=["POST"])
def user_register():
    email = request.args['email']
    password = request.args['password']
    screenname = request.args['screenname']
    user = User(email, screenname, password)
    db.session.add(user)
    db.session.commit()
    return('done')

@app.route("/testlogin", methods=["post"])
def test_check_login():
    email = request.args['email']
    password = request.args['password']
    return check_login(email, password)

def check_login(emailid, password):
    user = User.query.filter_by(emailid=emailid, password=password).first()
    if user:
        return("True")
    return("False")

# # app.run('127.0.0.1', 5000)
# socketio.run(app)

# def func_handler(msg):
#     print(msg)
# socketio.on_event('my event', func_handler)


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

