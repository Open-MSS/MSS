from flask_socketio import SocketIO
from flask import request
import logging

from models import Permission, User


class SocketsManager(object):
	"""Class with handler functions for socket related"""

	def __init__(self):
		super(SocketsManager, self).__init__()		
		self.rooms = []
		self.sockets = []


	def handle_connect(self):
		logging.debug(request.sid)

	def handle_start_event(self, json):
		logging.info('received json: ' + str(json))
		# authenticate socket
		token = json['token']
		user = User.verify_auth_token(token)
		if not user:
			return

		# fetch projects
		permissions = Permission.query.filter_by(u_id=user.id).all()

		# for all the p_id in permissions, there'd be chatrooms in self.rooms
		# search and add user to respective rooms
		for permission in permissions:
			print(permission.p_id, permission.u_id)

		socket_storage = {
			'id': request.sid,
			'emailid': user.emailid
		}
		self.sockets.append(socket_storage)

	def handle_disconnect(self):
		logging.info("disconnected")
		logging.info(request.sid)
		# remove socket from socket_storage
		self.sockets[:] = [d for d in self.sockets if d['id'] != request.sid]
