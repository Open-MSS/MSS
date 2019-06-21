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
import os

from mslib.mscolab.models import db, Project, Permission, User
from mslib.mscolab.conf import MSCOLAB_DATA_DIR, STUB_CODE


class FileManager(object):
    """Class with handler functions for file related functionalities"""

    def __init__(self):
        pass

    def create_project(self, path, description, user):
        """
        path: path to the project
        description: description of the project
        """
        proj_available = Project.query.filter_by(path=path).first()
        if proj_available:
            return False
        project = Project(path, description)
        db.session.add(project)
        db.session.flush()
        project_id = project.id
        perm = Permission(user.id, project_id, "admin")
        db.session.add(perm)
        db.session.commit()
        data = fs.open_fs(MSCOLAB_DATA_DIR)
        project_file = data.open(project.path, 'w')
        project_file.write(STUB_CODE)
        return True

    def add_permission(self, p_id, u_id, access_level, user):
        """
        p_id: project id
        u_id: user-id who is being given permission
        access_level: the access level given to user
        user: authorized user, making this request
        """
        if not self.is_admin(user.id, p_id):
            return False
        perm_old = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if perm_old:
            return False
        perm_new = Permission(u_id, p_id, access_level)
        db.session.add(perm_new)
        db.session.commit()
        return True

    def revoke_permission(self, p_id, u_id, user):
        """
        p_id: project id
        u_id: user-id
        user: logged in user
        """
        deleted = None
        if user.id == u_id:
            return False
        if not self.is_admin(user.id, p_id):
            return False
        else:
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
            projects.append({"p_id": permission.p_id, "access_level": permission.access_level})
        return projects

    def is_admin(self, u_id, p_id):
        """
        p_id: project id
        u_id: user-id
        """
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not perm:
            return False
        elif perm.access_level != "admin":
            return False
        return True

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
            oldpath = os.path.join(MSCOLAB_DATA_DIR, project.path)
            newpath = os.path.join(MSCOLAB_DATA_DIR, value)
            if os.path.exists(newpath):
                return False
            os.rename(oldpath, newpath)
        setattr(project, attribute, value)
        db.session.commit()
        return True

    def update_access_level(self, p_id, u_id, access_level, user):
        if not self.is_admin(user.id, p_id):
            return False
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not perm:
            return False
        perm.access_level = access_level
        db.session.commit()
        return True

    def delete_file(self, p_id, user):
        """
        p_id: project id
        user: logged in user
        """
        if not self.is_admin(user.id, p_id):
            return False
        Permission.query.filter_by(p_id=p_id).delete()
        project = Project.query.filter_by(id=p_id).first()
        os.remove(os.path.join(MSCOLAB_DATA_DIR, project.path))
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

    def save_file(self, p_id, content):
        """
        p_id: project-id,
        content: content of the file to be saved
        # ToDo save change in schema
        """
        project = Project.query.filter_by(id=p_id).first()
        if not project:
            return False
        data = fs.open_fs(MSCOLAB_DATA_DIR)
        project_file = data.open(project.path, 'w')
        return project_file.write(content)

    def get_file(self, p_id, user):
        """
        p_id: project-id
        """
        perm = Permission.query.filter_by(u_id=user.id, p_id=p_id).first()
        if not perm:
            return False
        project = Project.query.filter_by(id=p_id).first()
        if not project:
            return False
        data = fs.open_fs(MSCOLAB_DATA_DIR)
        project_file = data.open(project.path, 'r')
        return project_file.read()
