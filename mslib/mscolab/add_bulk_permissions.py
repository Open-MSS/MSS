# -*- coding: utf-8 -*-
"""

    mslib.mscolab.add_bulk_permissions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is used to insert permissions in bulk to mscolab db. This would in future, be
    evolved to a circle management module, to deal with groups of users(circles).

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

from flask import Flask
import logging
import sys

from mslib.mscolab.models import User, db, Project, Permission
from mslib.mscolab.conf import mscolab_settings

logging.getLogger().setLevel(logging.INFO)
# set the project root directory as the static folder
app = Flask(__name__, static_url_path='')
app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = 'secret!'.encode('utf-8')
db.init_app(app)
path = sys.argv[1]


def main():
    with app.app_context():
        file = open(path, 'r')
        content = file.read()
        groups = content.split('\n\n')
        for group in groups:
            group = group.split('\n')
            p = Project.query.filter_by(path=group[0]).first()
            if p is None:
                logging.info("Project {} doesn't exist, please create it.")
                continue
            users = group[1:]
            for user in users:
                _username = user.split('-')[0]
                permission = user.split('-')[1]
                if permission == 'a':
                    permission = 'admin'
                elif permission == 'c':
                    permission = 'collaborator'
                else:
                    permission = 'viewer'

                u = User.query.filter_by(username=_username).first()
                if u is None:
                    logging.info("User {} doesn't exist, skipping entry".format(_username))
                    continue
                perm_existing = Permission.query.filter_by(u_id=u.id, p_id=p.id).first()
                if perm_existing:
                    logging.info("permission exists, skipping entry")
                    continue
                perm = Permission(u.id, p.id, permission)
                db.session.add(perm)
                db.session.commit()


if __name__ == "__main__":
    main()
