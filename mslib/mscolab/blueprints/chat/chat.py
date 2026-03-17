import json

from flask import Blueprint, request, g, jsonify

from mslib.mscolab.message_type import MessageType
from mslib.mscolab.models import Change
from mslib.mscolab.utils import get_message_dict
from mslib.mscolab.blueprints.auth.auth import verify_user

CHAT_BP = Blueprint('chat', __name__)


@CHAT_BP.route('/undo_changes', methods=["POST"])
@verify_user
def undo_changes():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo_changes(ch_id, user)
    # get op_id from change
    ch = Change.query.filter_by(id=ch_id).first()
    if result is True:
        sockio = getConfig()[1]
        sockio.sm.emit_file_change(ch.op_id)
    return str(result)


@CHAT_BP.route("/messages", methods=["GET"])
@verify_user
def messages():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    user = g.user
    op_id = request.args.get("op_id", request.form.get("op_id", None))

    if fm.is_member(user.id, op_id):
        cm = getConfig()[2]
        timestamp = request.args.get("timestamp", request.form.get("timestamp", "1970-01-01T00:00:00+00:00"))
        chat_messages = cm.get_messages(op_id, timestamp)
        return jsonify({"messages": chat_messages})
    return "False"


@CHAT_BP.route("/message_attachment", methods=["POST"])
@verify_user
def message_attachment():
    user = g.user
    op_id = request.form.get("op_id", None)
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    if fm.is_member(user.id, op_id):
        file = request.files['file']
        message_type = MessageType(int(request.form.get("message_type")))
        user = g.user
        users = fm.fetch_users_without_permission(int(op_id), user.id)
        if users is False:
            return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
        if file is not None:
            static_file_path = fm.upload_file(file, subfolder=str(op_id), include_prefix=True)
            if static_file_path is not None:
                cm = getConfig()[2]
                sockio = getConfig()[1]
                new_message = cm.add_message(user, static_file_path, op_id, message_type)
                new_message_dict = get_message_dict(new_message)
                sockio.emit('chat-message-client', json.dumps(new_message_dict))
                return jsonify({"success": True, "path": static_file_path})
            else:
                return "False"
        return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
    # normal use case never gets to this
    return "False"


@CHAT_BP.route('/get_all_changes', methods=['GET'])
@verify_user
def get_all_changes():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    named_version = request.args.get('named_version') == "True"
    user = g.user
    result = fm.get_all_changes(int(op_id), user, named_version)
    if result is False:
        jsonify({"success": False, "message": "Some error occurred!"})
    return jsonify({"success": True, "changes": result})


@CHAT_BP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    ch_id = int(request.args.get('ch_id', request.form.get('ch_id', 0)))
    user = g.user
    result = fm.get_change_content(ch_id, user)
    if result is False:
        return "False"
    return jsonify({"content": result})


@CHAT_BP.route('/set_version_name', methods=['POST'])
@verify_user
def set_version_name():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    ch_id = int(request.form.get('ch_id', 0))
    op_id = int(request.form.get('op_id', 0))
    version_name = request.form.get('version_name', None)
    u_id = g.user.id
    success = fm.set_version_name(ch_id, op_id, u_id, version_name)
    if success is False:
        return jsonify({"success": False, "message": "Some error occurred!"})

    return jsonify({"success": True, "message": "Successfully set version name"})
