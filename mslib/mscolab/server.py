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


@app.route("/")
def hello():
    return("Testing mscolab server")

@app.route("/register", methods=["POST"])
def user_register():
    email = request.args['email']
    password = request.args['password']
    screenname = request.args['screenname']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO MyUsers(emailid, password, screenname) VALUES (%s, %s)", (email, password, screenname))
    result = cur.fetchone()
    print(result)
    mysql.connection.commit()
    cur.close()

def check_login(emailid, password):
    cur = mysql.connection.cursor()
    cur.execute("SELECT FROM MyUsers WHERE emailid=%s and password=%s".format(emailid, password))
    result = cur.fetchone()
    if result:
        return True
    return False

# # app.run('127.0.0.1', 5000)
# socketio.run(app)

# def func_handler(msg):
#     print(msg)
# socketio.on_event('my event', func_handler)



@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on('connect')
def handle_connect():
    print("connected")
    # send a small key to user to identify with, for now use usernames
if __name__ == '__main__':
    socketio.run(app)

