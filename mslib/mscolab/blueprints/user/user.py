import json
from pathlib import Path

from flask import Blueprint, g, request, jsonify, send_from_directory

from mslib.mscolab.app import APP
from mslib.mscolab.blueprints.auth.auth import verify_user

USER_BP = Blueprint('user', __name__)


@USER_BP.route('/user', methods=["GET"])
@verify_user
def get_user():
    return json.dumps({'user': {'id': g.user.id, 'username': g.user.username, 'fullname': g.user.fullname}})


@USER_BP.route('/upload_profile_image', methods=["POST"])
@verify_user
def upload_profile_image():
    user_id = g.user.id
    file = request.files['image']
    if not file:
        return jsonify({'message': 'No file provided or invalid file type'}), 400
    if not file.mimetype.startswith('image/'):
        return jsonify({'message': 'Invalid file type'}), 400
    if file.content_length > APP.config['MAX_UPLOAD_SIZE']:
        return jsonify({'message': 'File too large'}), 413
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    success, message = fm.save_user_profile_image(user_id, file)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


@USER_BP.route('/fetch_profile_image', methods=["GET"])
@verify_user
def fetch_profile_image():
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    user_id = request.form['user_id']
    success, filename = fm.get_user_profile_image(user_id)
    if success:
        base_path = APP.config['UPLOAD_FOLDER']
        return send_from_directory(Path(base_path), filename)
    else:
        return jsonify({'message': 'User or profile image not found'}), 404


@USER_BP.route("/delete_own_account", methods=["POST"])
@verify_user
def delete_own_account():
    """
    delete own account
    """
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    user = g.user
    result = fm.modify_user(user, action="delete")
    return jsonify({"success": result}), 200
