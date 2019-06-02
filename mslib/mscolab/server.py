from flask import Flask, request
app = Flask(__name__)

from flask_mysqldb import MySQL
from flask_socketio import SocketIO
import sys

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pop12345'
app.config['MYSQL_DB'] = 'mscolab'

mysql = MySQL(app)

sockets = []

@app.route("/")
def hello():
    return("Testing mscolab server")

@app.route("/register", methods=["POST"])
def user_register():
    email = request.args['email']
    password = request.args['password']
    screenname = request.args['screenname']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(emailid, password, screenname) VALUES (%s, %s, %s)", (email, password, screenname))
    result = cur.fetchone()
    print(result)
    mysql.connection.commit()
    cur.close()
    return('done')

@app.route("/testlogin", methods=["post"])
def test_check_login():
    email = request.args['email']
    password = request.args['password']
    return check_login(email, password)

def check_login(emailid, password):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE emailid=%s and password=%s;", (emailid, password))
    result = cur.fetchone()
    mysql.connection.commit()
    cur.close()
    if result:
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

