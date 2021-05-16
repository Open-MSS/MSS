# -*- coding: utf-8 -*-
"""

    mslib.mscolab.file_manager.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle file I/O in mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
import fs
import difflib
import logging
import git
from sqlalchemy.exc import IntegrityError
from mslib.mscolab.models import db, Project, Permission, User, Change, Message
from mslib.mscolab.conf import mscolab_settings


class FileManager(object):
    """Class with handler functions for file related functionalities"""

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def create_project(self, path, description, user, content=None):
        """
        path: path to the project
        description: description of the project
        """
        # set codes on these later
        if path.find("/") != -1 or path.find("\\") != -1 or (" " in path):
            logging.debug("malicious request: %s", user)
            return False
        proj_available = Project.query.filter_by(path=path).first()
        if proj_available:
            return False
        project = Project(path, description)
        db.session.add(project)
        db.session.flush()
        project_id = project.id
        # this is the only insertion with "creator" access_level
        perm = Permission(user.id, project_id, "creator")
        db.session.add(perm)
        db.session.commit()
        data = fs.open_fs(self.data_dir)
        data.makedir(project.path)
        project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'w')
        if content is not None:
            project_file.write(content)
        else:
            project_file.write(mscolab_settings.STUB_CODE)
        project_path = fs.path.combine(self.data_dir, project.path)
        r = git.Repo.init(project_path)
        r.git.clear_cache()
        r.index.add(['main.ftml'])
        r.index.commit("initial commit")
        return True

    def get_project_details(self, p_id, user):
        """
        p_id: project id
        user: authenticated user
        """
        project = Project.query.filter_by(id=p_id).first()
        project = {
            "id": project.id,
            "path": project.path,
            "description": project.description
        }
        return project

    def list_projects(self, user):
        """
        user: logged in user
        """
        projects = []
        permissions = Permission.query.filter_by(u_id=user.id).all()
        for permission in permissions:
            project = Project.query.filter_by(id=permission.p_id).first()
            projects.append({
                "p_id": permission.p_id,
                "access_level": permission.access_level,
                "path": project.path,
                "description": project.description
            })
        return projects

    def is_admin(self, u_id, p_id):
        """
        p_id: project id
        u_id: user-id
        """
        # return true only if the user is admin or creator
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not perm:
            return False
        elif perm.access_level != "admin" and perm.access_level != "creator":
            return False
        return True

    def auth_type(self, u_id, p_id):
        """
        p_id: project id
        u_id: user-id
        """
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not perm:
            return False
        return perm.access_level

    def update_project(self, p_id, attribute, value, user):
        """
        p_id: project id
        attribute: attribute to be changed, eg path
        user: logged in user
        """
        if not self.is_admin(user.id, p_id):
            return False
        project = Project.query.filter_by(id=p_id).first()
        if attribute == "path":
            if value.find("/") != -1 or value.find("\\") != -1 or (" " in value):
                logging.debug("malicious request: %s", user)
                return False
            data = fs.open_fs(self.data_dir)
            if data.exists(value):
                return False
            # will be move when projects are introduced
            # make a directory, else movedir
            data.makedir(value)
            data.movedir(project.path, value)
        setattr(project, attribute, value)
        db.session.commit()
        return True

    def delete_file(self, p_id, user):
        """
        p_id: project id
        user: logged in user
        """
        if self.auth_type(user.id, p_id) != "creator":
            return False
        Permission.query.filter_by(p_id=p_id).delete()
        Change.query.filter_by(p_id=p_id).delete()
        Message.query.filter_by(p_id=p_id).delete()
        project = Project.query.filter_by(id=p_id).first()
        with fs.open_fs(self.data_dir) as project_dir:
            project_dir.removetree(project.path)
        db.session.delete(project)
        db.session.commit()
        return True

    def get_authorized_users(self, p_id):
        """
        p_id: project-id
        """
        permissions = Permission.query.filter_by(p_id=p_id).all()
        users = []
        for permission in permissions:
            user = User.query.filter_by(id=permission.u_id).first()
            users.append({"username": user.username, "access_level": permission.access_level})
        return users

    def save_file(self, p_id, content, user, comment=""):
        """
        p_id: project-id,
        content: content of the file to be saved
        # ToDo save change in schema
        """
        project = Project.query.filter_by(id=p_id).first()
        if not project:
            return False

        with fs.open_fs(self.data_dir) as data:
            """
            old file is read, the diff between old and new is calculated and stored
            as 'Change' in changes table. comment for each change is optional
            """
            old_data = data.readtext(fs.path.combine(project.path, 'main.ftml'))
            old_data_lines = old_data.splitlines()
            content_lines = content.splitlines()
            diff = difflib.unified_diff(old_data_lines, content_lines, lineterm='')
            diff_content = '\n'.join(list(diff))
            data.writetext(fs.path.combine(project.path, 'main.ftml'), content)
        # commit changes if comment is not None
        if diff_content != "":
            # commit to git repository
            project_path = fs.path.combine(self.data_dir, project.path)
            repo = git.Repo(project_path)
            repo.git.clear_cache()
            repo.index.add(['main.ftml'])
            cm = repo.index.commit("committing changes")
            # change db table
            change = Change(p_id, user.id, cm.hexsha)
            db.session.add(change)
            db.session.commit()
            return True
        return False

    def get_file(self, p_id, user):
        """
        p_id: project-id
        user: user of this request
        """
        perm = Permission.query.filter_by(u_id=user.id, p_id=p_id).first()
        if not perm:
            return False
        project = Project.query.filter_by(id=p_id).first()
        if not project:
            return False
        with fs.open_fs(self.data_dir) as data:
            project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'r')
            project_data = project_file.read()
        return project_data

    def get_all_changes(self, p_id, user, named_version=None):
        """
        p_id: project-id
        user: user of this request

        Get all changes, mostly to be used in the chat window, in the side panel
        to render the recent changes.
        """
        perm = Permission.query.filter_by(u_id=user.id, p_id=p_id).first()
        if not perm:
            return False
        # Get all changes
        if named_version is None:
            changes = Change.query.\
                filter_by(p_id=p_id)\
                .order_by(Change.created_at.desc())\
                .all()
        # Get only named versions
        else:
            changes = Change.query\
                .filter(Change.p_id == p_id)\
                .filter(~Change.version_name.is_(None))\
                .order_by(Change.created_at.desc())\
                .all()

        return list(map(lambda change: {
            'id': change.id,
            'comment': change.comment,
            'version_name': change.version_name,
            'username': change.user.username,
            'created_at': change.created_at.strftime("%Y-%m-%d, %H:%M:%S")
        }, changes))

    def get_change_content(self, ch_id):
        """
        ch_id: change id
        user: user of this request

        Get change related to id
        """
        change = Change.query.filter_by(id=ch_id).first()
        if not change:
            return False
        project = Project.query.filter_by(id=change.p_id).first()
        project_path = fs.path.combine(self.data_dir, project.path)
        repo = git.Repo(project_path)
        change_content = repo.git.show(f'{change.commit_hash}:main.ftml')
        return change_content

    def set_version_name(self, ch_id, p_id, u_id, version_name):
        if not self.is_admin(u_id, p_id):
            return False
        Change.query\
            .filter(Change.id == ch_id)\
            .update({Change.version_name: version_name}, synchronize_session=False)
        db.session.commit()
        return True

    def undo(self, ch_id, user):
        """
        ch_id: change-id
        user: user of this request

        Undo a change
        # ToDo a revert option, which removes only that commit's change
        """
        ch = Change.query.filter_by(id=ch_id).first()
        if not self.is_admin(user.id, ch.p_id):
            return False
        if ch is None:
            return False
        project = Project.query.filter_by(id=ch.p_id).first()
        if not ch or not project:
            return False

        project_path = fs.path.join(self.data_dir, project.path)
        repo = git.Repo(project_path)
        repo.git.clear_cache()
        try:
            file_content = repo.git.show(f'{ch.commit_hash}:main.ftml')
            with fs.open_fs(project_path) as proj_fs:
                proj_fs.writetext('main.ftml', file_content)
            repo.index.add(['main.ftml'])
            cm = repo.index.commit(f"checkout to {ch.commit_hash}")
            change = Change(ch.p_id, user.id, cm.hexsha)
            db.session.add(change)
            db.session.commit()
            return True
        except Exception as ex:
            logging.debug(ex)
            return False

    def fetch_users_without_permission(self, p_id, u_id):
        if not self.is_admin(u_id, p_id):
            return False

        user_list = User.query\
            .join(Permission, (User.id == Permission.u_id) & (Permission.p_id == p_id), isouter=True) \
            .add_columns(User.id, User.username) \
            .filter(Permission.u_id.is_(None))

        users = [[user.username, user.id] for user in user_list]
        return users

    def fetch_users_with_permission(self, p_id, u_id):
        if not self.is_admin(u_id, p_id):
            return False

        user_list = User.query\
            .join(Permission, User.id == Permission.u_id)\
            .add_columns(User.id, User.username, Permission.access_level) \
            .filter(Permission.p_id == p_id) \
            .filter((User.id != u_id) & (Permission.access_level != 'creator'))

        users = [[user.username, user.access_level, user.id] for user in user_list]
        return users

    def add_bulk_permission(self, p_id, user, new_u_ids, access_level):
        if not self.is_admin(user.id, p_id):
            return False

        new_permissions = []
        for u_id in new_u_ids:
            new_permissions.append(Permission(u_id, p_id, access_level))
        db.session.add_all(new_permissions)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    def modify_bulk_permission(self, p_id, user, u_ids, new_access_level):
        if not self.is_admin(user.id, p_id):
            return False

        # TODO: Check whether we need synchronize_session False Or Fetch
        Permission.query\
            .filter(Permission.p_id == p_id)\
            .filter(Permission.u_id.in_(u_ids))\
            .update({Permission.access_level: new_access_level}, synchronize_session='fetch')

        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    def delete_bulk_permission(self, p_id, user, u_ids):
        if not self.is_admin(user.id, p_id):
            return False

        Permission.query \
            .filter(Permission.p_id == p_id) \
            .filter(Permission.u_id.in_(u_ids)) \
            .delete(synchronize_session='fetch')

        db.session.commit()
        return True

    def import_permissions(self, import_p_id, current_p_id, u_id):
        if not self.is_admin(u_id, current_p_id):
            return False, None

        perm = Permission.query.filter_by(u_id=u_id, p_id=import_p_id).first()
        if not perm:
            return False, None

        existing_perms = Permission.query \
            .filter(Permission.p_id == current_p_id) \
            .filter((Permission.u_id != u_id) & (Permission.access_level != 'creator')) \
            .all()

        current_project_creator = Permission.query.filter_by(p_id=current_p_id, access_level="creator").first()
        import_perms = Permission.query\
            .filter(Permission.p_id == import_p_id)\
            .filter((Permission.u_id != u_id) & (Permission.u_id != current_project_creator.u_id))\
            .all()

        # We Delete all the existing permissions
        existing_users = []
        for perm in existing_perms:
            existing_users.append(perm.u_id)
            db.session.delete(perm)

        db.session.flush()

        # Then add the permissions of the imported project
        new_users = []
        for perm in import_perms:
            access_level = perm.access_level
            if perm.access_level == "creator":
                access_level = "admin"
            new_users.append(perm.u_id)
            db.session.add(Permission(perm.u_id, current_p_id, access_level))

        # Set Difference of lists new_users - existing users
        add_users = [u_id for u_id in new_users if u_id not in existing_users]
        # Intersection of lists existing_users and new_users
        modify_users = [u_id for u_id in existing_users if u_id in new_users]
        # Set Difference of lists existing users - new_users
        delete_users = [u_id for u_id in new_users if u_id in existing_users]

        try:
            db.session.commit()
            return True, {"add_users": add_users, "modify_users": modify_users, "delete_users": delete_users}

        except IntegrityError:
            db.session.rollback()
            return False, None
