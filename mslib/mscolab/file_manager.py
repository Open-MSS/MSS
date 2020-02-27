# -*- coding: utf-8 -*-
"""

    mslib.mscolab.file_manager.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle file I/O in mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
        project = Project(path, description, False)
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
        r.index.add(['main.ftml'])
        r.index.commit("initial commit")
        return True

    def get_project_details(self, p_id, user):
        """
        p_id: project id
        user: authenticated user
        """
        project = Project.query.filter_by(id=p_id).first()
        project = {"id": project.id,
                   "path": project.path,
                   "description": project.description,
                   "autosave": project.autosave
                   }
        return project

    def add_permission(self, p_id, u_id, username, access_level, user):
        """
        p_id: project id
        u_id: user-id who is being given permission
        access_level: the access level given to user
        user: authorized user, making this request
        """
        if not self.is_admin(user.id, p_id):
            return False
        if username:
            user_victim = User.query.filter((User.username == username) | (User.emailid == username)).first()
            if not user_victim:
                return False
            u_id = user_victim.id
        perm_old = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if perm_old or (access_level == "creator"):
            return False
        perm_new = Permission(u_id, p_id, access_level)
        db.session.add(perm_new)
        db.session.commit()
        return True

    def revoke_permission(self, p_id, u_id, username, user):
        """
        p_id: project id
        u_id: user-id
        username: to identify victim user
        user: logged in user
        """
        deleted = None
        if user.id == u_id:
            return False
        if not self.is_admin(user.id, p_id):
            return False
        else:
            if username:
                user_victim = User.query.filter((User.username == username) | (User.emailid == username)).first()
                if not user_victim:
                    return False
                u_id = user_victim.id
            perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
            if perm is None:
                return False
            if perm.access_level == "creator":
                return False
            deleted = Permission.query.filter_by(u_id=u_id, p_id=p_id).delete()
            db.session.commit()
        if deleted:
            return True
        else:
            return False

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
                            "description": project.description,
                            "autosave": project.autosave})
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
            # make a directory, else movedir fails
            data.makedir(value)
            data.movedir(project.path, value)
        setattr(project, attribute, value)
        db.session.commit()
        return True

    def update_access_level(self, p_id, u_id, username, access_level, user):
        if not self.is_admin(user.id, p_id):
            return False
        if username:
            user_victim = User.query.filter((User.username == username) | (User.emailid == username)).first()
            if not user_victim:
                return False
            u_id = user_victim.id
        if u_id is None or u_id == user.id:
            return
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not perm or perm.access_level == "creator":
            return False
        perm.access_level = access_level
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
        Change.query.filter_by(p_id=p_id).delete()
        project = Project.query.filter_by(id=p_id).first()
        data = fs.open_fs(self.data_dir)
        data.removetree(project.path)
        project = Project.query.filter_by(id=p_id).delete()
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
        data = fs.open_fs(self.data_dir)
        """
        old file is read, the diff between old and new is calculated and stored
        as 'Change' in changes table. comment for each change is optional
        """
        project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'r')
        old_data = project_file.read()
        project_file.close()
        old_data_lines = old_data.splitlines()
        content_lines = content.splitlines()
        diff = difflib.unified_diff(old_data_lines, content_lines, lineterm='')
        diff_content = '\n'.join(list(diff))
        project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'w')
        project_file.write(content)
        project_file.close()
        # commit changes if comment is not None
        if diff_content != "":
            # commit to git repository
            project_path = fs.path.combine(self.data_dir, project.path)
            repo = git.Repo(project_path)
            repo.index.add(['main.ftml'])
            # hack used, ToDo fix it
            if comment == "" or comment is False or comment is None:
                comment = "committing change"
            cm = repo.index.commit(comment)
            # change db table
            change = Change(p_id, user.id, diff_content, cm.hexsha, comment)
            db.session.add(change)
            db.session.commit()
        return True

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
        data = fs.open_fs(self.data_dir)
        project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'r')
        return project_file.read()

    def get_changes(self, p_id, user):
        """
        p_id: project-id
        user: user of this request

        Get all changes, mostly to be used in the chat window, in the side panel
        to render the recent changes.
        """
        perm = Permission.query.filter_by(u_id=user.id, p_id=p_id).first()
        if not perm:
            return False
        changes = Change.query.filter_by(p_id=p_id).all()
        return list(map(lambda change: {'content': change.content,
                                        'comment': change.comment,
                                        'u_id': change.u_id,
                                        'username': self.get_user_from_id(change.u_id).username,
                                        'id': change.id}, changes,))

    def get_user_from_id(self, id):
        return User.query.filter_by(id=id).first()

    def get_change_by_id(self, ch_id, user):
        """
        ch_id: change id
        user: user of this request

        Get change related to id
        """
        change = Change.query.filter_by(id=ch_id).first()
        if not change:
            return False
        perm = Permission.query.filter_by(u_id=user.id, p_id=change.p_id).first()
        if not perm:
            return False
        return {'content': change.content, 'comment': change.comment, 'u_id': change.u_id}

    def undo(self, ch_id, user):
        """
        ch_id: change-id
        user: user of this request

        Undo a change
        # ToDo a revert option, which removes only that commit's change
        """
        ch = Change.query.filter_by(id=ch_id).first()
        if ch is None:
            return False
        project = Project.query.filter_by(id=ch.p_id).first()
        if not ch or not project:
            return False

        data = fs.open_fs(self.data_dir)
        project_file = data.open(fs.path.combine(project.path, 'main.ftml'), 'r')
        old_data = project_file.read()
        project_file.close()
        old_data_lines = old_data.splitlines()

        project_path = fs.path.combine(self.data_dir, project.path)
        repo = git.Repo(project_path)
        try:
            file_content = repo.git.show('{}:{}'.format(ch.commit_hash, 'main.ftml'))

            content_lines = file_content.splitlines()
            diff = difflib.unified_diff(old_data_lines, content_lines, lineterm='')
            diff_content = '\n'.join(list(diff))

            proj_fs = fs.open_fs(project_path)
            proj_fs.writetext('main.ftml', file_content)
            proj_fs.close()
            repo.index.add(['main.ftml'])
            cm = repo.index.commit("checkout to {}".format(ch.commit_hash))

            change = Change(ch.p_id, user.id, diff_content, cm.hexsha,
                            "checkout to {}".format(ch.commit_hash))
            db.session.add(change)
            db.session.commit()

            return True
        except Exception as ex:
            logging.debug(ex)
            return False
