# -*- coding: utf-8 -*-
"""

    mslib.mscolab.file_manager.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle file I/O in mscolab

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import sys
import secrets
import time
import datetime
import fs
import difflib
import logging
import git
import threading
import mimetypes
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from mslib.utils.verify_waypoint_data import verify_waypoint_data
from mslib.mscolab.models import db, Operation, Permission, User, Change, Message
from mslib.mscolab.conf import mscolab_settings


class FileManager:
    """Class with handler functions for file related functionalities"""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.operation_dict_lock = threading.Lock()
        self.operation_locks = {}

    def _get_operation_lock(self, op_id):
        with self.operation_dict_lock:
            try:
                return self.operation_locks[op_id]
            except KeyError:
                self.operation_locks[op_id] = threading.Lock()
                return self.operation_locks[op_id]

    def create_operation(self, path, description, user, last_used=None, content=None, category="default", active=True):
        """
        Creates a new operation in the mscolab system.

        :param path: The path of the operation.
        :param description: The description of the operation.
        :param user: The user object creating the operation.
        :param last_used: The last used datetime of the operation. Default is None.
        :param content: The content of the operation. Default is None.
        :param category: The category of the operation. Default is 'default'.
        :param active: The activity status of the operation. Default is True.
        :return: True if the operation is created successfully, False otherwise.
        """
        if content is not None and not verify_waypoint_data(content):
            return False
        # set codes on these later
        if path.find("/") != -1 or path.find("\\") != -1 or (" " in path):
            logging.debug("malicious request: %s", user)
            return False
        proj_available = Operation.query.filter_by(path=path).first()
        if proj_available is not None:
            return False
        if last_used is None:
            last_used = datetime.datetime.now(tz=datetime.timezone.utc)
        operation = Operation(path, description, last_used, category, active=active)
        db.session.add(operation)
        db.session.flush()
        operation_id = operation.id

        op_lock = self._get_operation_lock(operation_id)
        with op_lock:
            # this is the only insertion with "creator" access_level
            perm = Permission(user.id, operation_id, "creator")
            db.session.add(perm)
            db.session.commit()
            # here we can import the permissions from Group file
            if not path.endswith(mscolab_settings.GROUP_POSTFIX):
                import_op = Operation.query.filter_by(path=f"{category}{mscolab_settings.GROUP_POSTFIX}").first()
                if import_op is not None:
                    self.import_permissions(import_op.id, operation_id, user.id)
            data = fs.open_fs(self.data_dir)
            data.makedir(operation.path)
            operation_file = data.open(fs.path.combine(operation.path, 'main.ftml'), 'w')
            if content is not None:
                operation_file.write(content)
            else:
                operation_file.write(mscolab_settings.STUB_CODE)
            operation_path = fs.path.combine(self.data_dir, operation.path)
            r = git.Repo.init(operation_path)
            r.git.clear_cache()
            r.index.add(['main.ftml'])
            r.index.commit("initial commit")
            return True

    def get_operation_details(self, op_id, user):
        """
        op_id: operation id
        user: authenticated user
        """
        if self.is_member(user.id, op_id):
            operation = Operation.query.filter_by(id=op_id).first()
            op = {
                "id": operation.id,
                "path": operation.path,
                "description": operation.description
            }
            return op
        return False

    def list_operations(self, user, skip_archived=False):
        """
        user: logged in user
        skip_archived: filter by active operations
        """
        operations = []
        permissions = Permission.query.filter_by(u_id=user.id).all()
        for permission in permissions:
            operation = Operation.query.filter_by(id=permission.op_id).first()
            if operation is not None and (operation.active or not skip_archived):
                operations.append({
                    "op_id": permission.op_id,
                    "access_level": permission.access_level,
                    "path": operation.path,
                    "description": operation.description,
                    "category": operation.category,
                    "active": operation.active
                })
        return operations

    def is_member(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        # return true only if the user is a member
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        return True

    def is_admin(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        # return true only if the user is admin
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        elif perm.access_level != "admin":
            return False
        return True

    def is_creator(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        # return true only if the user is creator
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        elif perm.access_level != "creator":
            return False
        return True

    def is_collaborator(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        # return true only if the user is collaborator
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        elif perm.access_level != "collaborator":
            return False
        return True

    def is_viewer(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        # return true only if the user is viewer
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        elif perm.access_level != "viewer":
            return False
        return True

    def auth_type(self, u_id, op_id):
        """
        op_id: operation id
        u_id: user-id
        """
        perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if perm is None:
            return False
        return perm.access_level

    def modify_user(self, user, attribute=None, value=None, action=None):
        if action == "create":
            user_query = User.query.filter_by(emailid=str(user.emailid)).first()
            if user_query is None:
                db.session.add(user)
                db.session.commit()
            else:
                return False
        elif action == "delete":
            user_query = User.query.filter_by(id=user.id).first()
            if user_query is not None:
                # Delete profile image if it exists
                if user.profile_image_path:
                    self.delete_user_profile_image(user.profile_image_path)
                db.session.delete(user)
                db.session.commit()
            user_query = User.query.filter_by(id=user.id).first()
            # on delete we return successful deleted
            if user_query is None:
                return True
        elif action == "update_idp_user":
            user_query = User.query.filter_by(emailid=str(user.emailid)).first()
            if user_query is not None:
                db.session.add(user)
                db.session.commit()
            else:
                return False
        user_query = User.query.filter_by(id=user.id).first()
        if user_query is None:
            return False
        if None not in (attribute, value):
            if attribute == "emailid":
                user_query = User.query.filter_by(emailid=str(value)).first()
                if user_query is not None:
                    return False
            setattr(user, attribute, value)
            db.session.commit()
        return True

    def delete_user_profile_image(self, image_to_be_deleted):
        '''
        This function is called when deleting account or updating the profile picture
        '''
        upload_folder = mscolab_settings.UPLOAD_FOLDER
        if sys.platform.startswith('win'):
            upload_folder = upload_folder.replace('\\', '/')

        with fs.open_fs(upload_folder) as profile_fs:
            if profile_fs.exists(image_to_be_deleted):
                profile_fs.remove(image_to_be_deleted)
                logging.debug(f"Successfully deleted image: {image_to_be_deleted}")

    def upload_file(self, file, subfolder=None, identifier=None, include_prefix=False):
        """
        Generic function to save files securely in any specified directory with unique filename
        and return the relative file path.
        """
        upload_folder = mscolab_settings.UPLOAD_FOLDER
        if sys.platform.startswith('win'):
            upload_folder = upload_folder.replace('\\', '/')

        subfolder_path = fs.path.join(upload_folder, str(subfolder) if subfolder else "")
        with fs.open_fs(subfolder_path, create=True) as _fs:
            # Creating unique and secure filename
            file_name, _ = file.filename.rsplit('.', 1)
            mime_type, _ = mimetypes.guess_type(file.filename)
            file_ext = mimetypes.guess_extension(mime_type) if mime_type else '.unknown'
            token = secrets.token_urlsafe()
            timestamp = time.strftime("%Y%m%dT%H%M%S")

            if identifier:
                file_name = f'{identifier}-{timestamp}-{token}{file_ext}'
            else:
                file_name = f'{file_name}-{timestamp}-{token}{file_ext}'
            file_name = secure_filename(file_name)

            # Saving the file
            with _fs.open(file_name, mode="wb") as f:
                file.save(f)

            # Relative File path
            if include_prefix:  # ToDo: add a namespace for the chat attachments, similar as for profile images
                static_dir = fs.path.basename(upload_folder)
                static_file_path = fs.path.join(static_dir, str(subfolder), file_name)
            else:
                static_file_path = fs.path.relativefrom(upload_folder, fs.path.join(subfolder_path, file_name))

            logging.debug(f'Relative Path: {static_file_path}')
            return static_file_path

    def save_user_profile_image(self, user_id, image_file):
        """
        Save the user's profile image path to the database.
        """
        relative_file_path = self.upload_file(image_file, subfolder='profile', identifier=user_id)

        user = User.query.get(user_id)
        if user:
            if user.profile_image_path:
                # Delete the previous image
                self.delete_user_profile_image(user.profile_image_path)
            user.profile_image_path = relative_file_path
            db.session.commit()
            return True, "Image uploaded successfully"
        else:
            return False, "User not found"

    def update_operation(self, op_id, attribute, value, user):
        """
        op_id: operation id
        attribute: attribute to be changed, eg path
        user: logged in user
        """
        if not self.is_admin(user.id, op_id) and not self.is_creator(user.id, op_id):
            return False
        operation = Operation.query.filter_by(id=op_id).first()
        if attribute == "path":
            if value.find("/") != -1 or value.find("\\") != -1 or (" " in value):
                logging.debug("malicious request: %s", user)
                return False
            with fs.open_fs(self.data_dir) as data:
                if data.exists(value):
                    return False
                # will be move when operations are introduced
                # make a directory, else movedir
                data.makedir(value)
                data.movedir(operation.path, value)
                # when renamed to a Group operation
            if value.endswith(mscolab_settings.GROUP_POSTFIX):
                # getting the category
                category = value.split(mscolab_settings.GROUP_POSTFIX)[0]
                # all operation with that category
                ops_category = Operation.query.filter_by(category=category)
                for ops in ops_category:
                    # the user changing the {category}{mscolab_settings.GROUP_POSTFIX} needs to have rights in the op
                    # then members of this op gets added to all others of same category
                    self.import_permissions(op_id, ops.id, user.id)
        elif attribute == "active":
            if isinstance(value, str):
                value = value.upper() == "TRUE"
        setattr(operation, attribute, value)
        db.session.commit()
        return True

    def delete_operation(self, op_id, user):
        """
        op_id: operation id
        user: logged in user
        """
        if not self.is_creator(user.id, op_id):
            return False
        Permission.query.filter_by(op_id=op_id).delete()
        Change.query.filter_by(op_id=op_id).delete()
        Message.query.filter_by(op_id=op_id).delete()
        operation = Operation.query.filter_by(id=op_id).first()
        with fs.open_fs(self.data_dir) as operation_dir:
            operation_dir.removetree(operation.path)
        db.session.delete(operation)
        db.session.commit()
        return True

    def get_authorized_users(self, op_id):
        """
        op_id: operation-id
        """
        permissions = Permission.query.filter_by(op_id=op_id).all()
        users = []
        for permission in permissions:
            user = User.query.filter_by(id=permission.u_id).first()
            users.append({"username": user.username, "access_level": permission.access_level,
                          "id": permission.u_id})
        return users

    def save_file(self, op_id, content, user, comment=""):
        """
        op_id: operation-id,
        content: content of the file to be saved
        # ToDo save change in schema
        """
        if not verify_waypoint_data(content):
            return False
        # ToDo use comment
        operation = Operation.query.filter_by(id=op_id).first()
        if not operation:
            return False

        op_lock = self._get_operation_lock(operation.id)
        with op_lock:
            with fs.open_fs(self.data_dir) as data:
                """
                old file is read, the diff between old and new is calculated and stored
                as 'Change' in changes table. comment for each change is optional
                """
                old_data = data.readtext(fs.path.combine(operation.path, 'main.ftml'))
                old_data_lines = old_data.splitlines()
                content_lines = content.splitlines()
                diff = difflib.unified_diff(old_data_lines, content_lines, lineterm='')
                diff_content = '\n'.join(list(diff))
                data.writetext(fs.path.combine(operation.path, 'main.ftml'), content)
            # commit changes if comment is not None
            if diff_content != "":
                # commit to git repository
                operation_path = fs.path.combine(self.data_dir, operation.path)
                repo = git.Repo(operation_path)
                repo.git.clear_cache()
                repo.index.add(['main.ftml'])
                cm = repo.index.commit("committing changes")
                # change db table
                change = Change(op_id, user.id, cm.hexsha)
                db.session.add(change)
                db.session.commit()
                return True
            return False

    def get_file(self, op_id, user):
        """
        op_id: operation-id
        user: user of this request
        """
        perm = Permission.query.filter_by(u_id=user.id, op_id=op_id).first()
        if perm is None:
            return False
        operation = Operation.query.filter_by(id=op_id).first()
        if operation is None:
            return False
        op_lock = self._get_operation_lock(op_id)
        with op_lock:
            with fs.open_fs(self.data_dir) as data:
                operation_file = data.open(fs.path.combine(operation.path, 'main.ftml'), 'r')
                operation_data = operation_file.read()
            return operation_data

    def get_all_changes(self, op_id, user, named_version=False):
        """
        op_id: operation-id
        user: user of this request

        Get all changes, mostly to be used in the chat window, in the side panel
        to render the recent changes.
        """
        perm = Permission.query.filter_by(u_id=user.id, op_id=op_id).first()
        if perm is None:
            return False
        # Get only named versions
        if named_version:
            changes = Change.query\
                .filter(Change.op_id == op_id)\
                .filter(~Change.version_name.is_(None))\
                .order_by(Change.created_at.desc())\
                .all()
        # Get all changes
        else:
            changes = Change.query\
                .filter_by(op_id=op_id)\
                .order_by(Change.created_at.desc())\
                .all()

        return list(map(lambda change: {
            'id': change.id,
            'comment': change.comment,
            'version_name': change.version_name,
            'username': change.user.username,
            'created_at': change.created_at.isoformat()
        }, changes))

    def get_change_content(self, ch_id, user):
        """
        ch_id: change id
        user: user of this request

        Get change related to id
        """
        ch = Change.query.filter_by(id=ch_id).first()
        perm = Permission.query.filter_by(u_id=user.id, op_id=ch.op_id).first()
        if perm is None:
            return False

        change = Change.query.filter_by(id=ch_id).first()
        if not change:
            return False
        operation = Operation.query.filter_by(id=change.op_id).first()
        operation_path = fs.path.combine(self.data_dir, operation.path)
        repo = git.Repo(operation_path)
        change_content = repo.git.show(f'{change.commit_hash}:main.ftml')
        return change_content

    def set_version_name(self, ch_id, op_id, u_id, version_name):
        if (not self.is_admin(u_id, op_id) and not self.is_creator(u_id, op_id) and not
                self.is_collaborator(u_id, op_id)):
            return False
        Change.query\
            .filter(Change.id == ch_id)\
            .update({Change.version_name: version_name}, synchronize_session=False)
        db.session.commit()
        return True

    def undo_changes(self, ch_id, user):
        """
        ch_id: change-id
        user: user of this request

        Undo a change
        # ToDo add a revert option, which removes only that commit's change
        """
        ch = Change.query.filter_by(id=ch_id).first()
        if (not self.is_admin(user.id, ch.op_id) and not self.is_creator(user.id, ch.op_id) and not
                self.is_collaborator(user.id, ch.op_id)):
            return False
        if ch is None:
            return False
        operation = Operation.query.filter_by(id=ch.op_id).first()
        if not ch or not operation:
            return False

        op_lock = self._get_operation_lock(operation.id)
        with op_lock:
            operation_path = fs.path.join(self.data_dir, operation.path)
            repo = git.Repo(operation_path)
            repo.git.clear_cache()
            try:
                file_content = repo.git.show(f'{ch.commit_hash}:main.ftml')
                with fs.open_fs(operation_path) as proj_fs:
                    proj_fs.writetext('main.ftml', file_content)
                repo.index.add(['main.ftml'])
                cm = repo.index.commit(f"checkout to {ch.commit_hash}")
                change = Change(ch.op_id, user.id, cm.hexsha)
                db.session.add(change)
                db.session.commit()
                return True
            except Exception as ex:
                logging.debug(ex)
                return False

    def fetch_users_without_permission(self, op_id, u_id):
        if not self.is_admin(u_id, op_id) and not self.is_creator(u_id, op_id):
            return False

        user_list = User.query\
            .join(Permission, (User.id == Permission.u_id) & (Permission.op_id == op_id), isouter=True) \
            .add_columns(User.id, User.username) \
            .filter(Permission.u_id.is_(None))

        users = [[user.username, user.id] for user in user_list]
        return users

    def fetch_users_with_permission(self, op_id, u_id):
        if not self.is_admin(u_id, op_id) and not self.is_creator(u_id, op_id):
            return False

        user_list = User.query\
            .join(Permission, User.id == Permission.u_id)\
            .add_columns(User.id, User.username, Permission.access_level) \
            .filter(Permission.op_id == op_id) \
            .filter((User.id != u_id) & (Permission.access_level != 'creator'))

        users = [[user.username, user.access_level, user.id] for user in user_list]
        return users

    def fetch_operation_creator(self, op_id, u_id):
        if not self.is_member(u_id, op_id):
            # any participant of the OP is allowed to see who is the creator
            return False
        current_operation_creator = Permission.query.filter_by(op_id=op_id, access_level="creator").first()
        return current_operation_creator.user.username

    def add_bulk_permission(self, op_id, user, new_u_ids, access_level):
        if not self.is_admin(user.id, op_id) and not self.is_creator(user.id, op_id):
            return False

        new_permissions = []
        for u_id in new_u_ids:
            if Permission.query.filter_by(u_id=u_id, op_id=op_id).first() is None:
                new_permissions.append(Permission(u_id, op_id, access_level))
        db.session.add_all(new_permissions)
        operation = Operation.query.filter_by(id=op_id).first()
        if operation.path.endswith(mscolab_settings.GROUP_POSTFIX):
            # the members of this gets added to all others of same category
            category = operation.path.split(mscolab_settings.GROUP_POSTFIX)[0]
            # all operation with that category
            ops_category = Operation.query.filter_by(category=category)
            new_permissions = []
            for ops in ops_category:
                if not ops.path.endswith(mscolab_settings.GROUP_POSTFIX):
                    new_permissions.append(Permission(u_id, ops.id, access_level))
                db.session.add_all(new_permissions)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    def modify_bulk_permission(self, op_id, user, u_ids, new_access_level):
        if not self.is_admin(user.id, op_id) and not self.is_creator(user.id, op_id):
            return False

        # TODO: Check whether we need synchronize_session False Or Fetch
        Permission.query\
            .filter(Permission.op_id == op_id)\
            .filter(Permission.u_id.in_(u_ids))\
            .update({Permission.access_level: new_access_level}, synchronize_session='fetch')

        operation = Operation.query.filter_by(id=op_id).first()
        if operation.path.endswith(mscolab_settings.GROUP_POSTFIX):
            # the members of this gets added to all others of same category
            category = operation.path.split(mscolab_settings.GROUP_POSTFIX)[0]
            # all operation with that category
            ops_category = Operation.query.filter_by(category=category)
            for ops in ops_category:
                Permission.query \
                    .filter(Permission.op_id == ops.id) \
                    .filter(Permission.u_id.in_(u_ids)) \
                    .update({Permission.access_level: new_access_level}, synchronize_session='fetch')
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    def delete_bulk_permission(self, op_id, user, u_ids):
        # if the user is not a member of the operation, return false
        if not self.is_member(user.id, op_id):
            return False
        elif not self.is_admin(user.id, op_id) and not self.is_creator(user.id, op_id):
            # if the user is a member but non-admin and non-creator, and is trying to remove any other user
            if len(u_ids) != 1 or user.id not in u_ids:
                return False
        else:
            # if the user is admin or creator and is trying to remove a user not in this operation
            for u_id in u_ids:
                if not self.is_member(u_id, op_id):
                    return False
            if self.is_creator(user.id, op_id):
                # if the user is creator and is trying to leave the operation, return false
                if user.id in u_ids:
                    return False

        Permission.query \
            .filter(Permission.op_id == op_id) \
            .filter(Permission.u_id.in_(u_ids)) \
            .delete(synchronize_session='fetch')

        operation = Operation.query.filter_by(id=op_id).first()
        if operation.path.endswith(mscolab_settings.GROUP_POSTFIX):
            # the members of this gets added to all others of same category
            category = operation.path.split(mscolab_settings.GROUP_POSTFIX)[0]
            # all operation with that category
            ops_category = Operation.query.filter_by(category=category)
            for ops in ops_category:
                Permission.query \
                    .filter(Permission.op_id == ops.id) \
                    .filter(Permission.u_id.in_(u_ids)) \
                    .delete(synchronize_session='fetch')

        db.session.commit()
        return True

    def import_permissions(self, import_op_id, current_op_id, u_id):
        if not self.is_creator(u_id, current_op_id) and not self.is_admin(u_id, current_op_id):
            return False, None, "Not the creator or admin of this operation"

        perm = Permission.query.filter_by(u_id=u_id, op_id=import_op_id).first()
        if perm is None:
            return False, None, "Not a member of this operation"

        existing_perms = Permission.query \
            .filter(Permission.op_id == current_op_id) \
            .filter((Permission.u_id != u_id) & (Permission.access_level != 'creator')) \
            .all()
        existing_users = set([perm.u_id for perm in existing_perms])

        current_operation_creator = Permission.query.filter_by(op_id=current_op_id, access_level="creator").first()
        import_perms = Permission.query\
            .filter(Permission.op_id == import_op_id)\
            .filter((Permission.u_id != u_id) & (Permission.u_id != current_operation_creator.u_id))\
            .all()
        import_users = set([perm.u_id for perm in import_perms])

        is_perm = []
        for perm in existing_perms:
            is_perm.append((perm.u_id, perm.access_level))
        new_perm = []
        for perm in import_perms:
            access_level = perm.access_level
            # we keep creator to the one created the operation, and substitute the imported to admin
            if perm.access_level == "creator":
                access_level = "admin"
            new_perm.append((perm.u_id, access_level))

        if sorted(new_perm) == sorted(is_perm):
            return False, None, "Permissions are already given"

        # We Delete all permissions of existing users which not in new permission
        delete_users = []
        for perm in existing_perms:
            if (perm.u_id, perm.access_level) not in new_perm:
                db.session.delete(perm)
                delete_users.append(perm.u_id)

        db.session.flush()

        # Then add the permissions of the imported operation based on new_perm
        new_users = []
        for u_id, access_level in new_perm:
            if not (u_id, access_level) in is_perm:
                new_users.append(u_id)
                if Permission.query.filter_by(u_id=u_id, op_id=current_op_id).first() is None:
                    db.session.add(Permission(u_id, current_op_id, access_level))

        # prepare events based on action done
        delete_users = list(existing_users.difference(import_users))
        add_users = list(import_users.difference(existing_users))
        modify_users = []
        _intersect_users = import_users.intersection(existing_users)
        _new_perm = dict(new_perm)
        _is_perm = dict(is_perm)
        for m_uid in _intersect_users:
            if _new_perm[m_uid] != _is_perm[m_uid]:
                modify_users.append(m_uid)

        try:
            db.session.commit()
            return True, {"add_users": add_users, "modify_users": modify_users, "delete_users": delete_users}, "success"

        except IntegrityError:
            db.session.rollback()
            return False, None, "Some error occurred! Could not import permissions. Please try again."
