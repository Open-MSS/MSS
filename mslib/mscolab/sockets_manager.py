from flask_socketio import SocketIO
from flask import request
import logging
class SocketsManager(object):
	"""Class with handler functions for socket related"""

	def __init__(self):
		super(SocketsManager, self).__init__()		
		self.rooms = []
		self.sockets = []


	def handle_connect(self):
		logging.debug(request.sid)
		# add to rooms

	def handle_start_event(self, json):
		logging.info('received json: ' + str(json))
		socket_storage = {
			'id': request.sid,
			'emailid': json['emailid']
		}
		self.sockets.append(socket_storage)

	def handle_disconnect(self):
		logging.info("disconnected")
		logging.info(request.sid)
		# remove socket from socket_storage
		self.sockets[:] = [d for d in self.sockets if d['id'] != request.sid]
