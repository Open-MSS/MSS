import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('connection established')
    sio.emit('my event', {'sf':'dummy event my event called'})
    print("wtf really")

@sio.on('my message')
def on_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})

@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')

sio.connect('http://localhost:5000')
sio.wait()
