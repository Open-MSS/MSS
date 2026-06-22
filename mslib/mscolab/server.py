# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
import logging
import datetime
import socketio
import sqlalchemy.exc
import flask_migrate
import hashlib

from flask import jsonify, request, current_app
from flask_mail import Mail
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from mslib.mscolab.app import create_app, APP
from mslib.mscolab.models import User
from mslib.mscolab.sockets_manager import _setup_managers
from mslib.mscolab.utils import create_files
from mslib.mscolab import migrations


def _handle_db_upgrade():
    from mslib.mscolab.models import db

    create_files()
    inspector = sqlalchemy.inspect(db.engine)
    existing_tables = inspector.get_table_names()
    if ("alembic_version" not in existing_tables and len(existing_tables) > 0) or (
        "alembic_version" in existing_tables
        and len(existing_tables) > 1
        and db.session.execute(sqlalchemy.text("SELECT * FROM alembic_version")).first() is None
    ):
        sys.exit(
            """Your database contains no alembic_version revision identifier, but it has a schema. This suggests \
that you have a pre-existing database but haven't followed the database migration instructions. To prevent damage to \
your database MSColab will abort. Please follow the documentation for a manual database migration from MSColab v8/v9."""
        )

    is_empty_database = len(existing_tables) == 0 or (
        len(existing_tables) == 1
        and "alembic_version" in existing_tables
        and db.session.execute(sqlalchemy.text("SELECT * FROM alembic_version")).first() is None
    )
    # If a database connection to migrate from is set and the target database is empty, then migrate the existing data
    if is_empty_database and APP.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] is not None:
        logging.info("The target database is empty and a database to migrate from is set, starting the data migration")
        source_engine = sqlalchemy.create_engine(APP.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'])
        source_metadata = sqlalchemy.MetaData()
        source_metadata.reflect(bind=source_engine)
        # Determine the previous MSColab version based on the database content and upgrade to the corresponding revision
        if "authentication_backend" in source_metadata.tables["users"].columns:
            # It should be v9
            flask_migrate.upgrade(directory=migrations.__path__[0], revision="c171019fe3ee")
        else:
            # It's probably v8
            flask_migrate.upgrade(directory=migrations.__path__[0], revision="92eaba86a92e")
        # Copy over the existing data
        target_engine = sqlalchemy.create_engine(APP.config['SQLALCHEMY_DATABASE_URI'])
        target_metadata = sqlalchemy.MetaData()
        target_metadata.reflect(bind=target_engine)
        with source_engine.connect() as src_connection, target_engine.connect() as target_connection:
            for table in source_metadata.sorted_tables:
                if table.name == "alembic_version":
                    # Do not migrate the alembic_version table!
                    continue
                logging.debug("Copying table %s", table.name)
                stmt = target_metadata.tables[table.name].insert()
                for row in src_connection.execute(table.select()):
                    logging.debug("Copying row %s", row)
                    row = tuple(
                        r.replace(tzinfo=datetime.timezone.utc) if isinstance(r, datetime.datetime) else r for r in row
                    )
                    target_connection.execute(stmt.values(row))
            target_connection.commit()
            if target_engine.name == "postgresql":
                # Fix the databases auto-increment sequences, if it is a PostgreSQL database
                # For reference, see: https://wiki.postgresql.org/wiki/Fixing_Sequences
                logging.info("Using a PostgreSQL database, will fix up sequences")
                cur = target_connection.execute(sqlalchemy.text(r"""
SELECT
    'SELECT SETVAL(' ||
    quote_literal(quote_ident(sequence_namespace.nspname) || '.' || quote_ident(class_sequence.relname)) ||
    ', COALESCE(MAX(' ||quote_ident(pg_attribute.attname)|| '), 1) ) FROM ' ||
    quote_ident(table_namespace.nspname)|| '.'||quote_ident(class_table.relname)|| ';'
FROM pg_depend
    INNER JOIN pg_class AS class_sequence
        ON class_sequence.oid = pg_depend.objid
            AND class_sequence.relkind = 'S'
    INNER JOIN pg_class AS class_table
        ON class_table.oid = pg_depend.refobjid
    INNER JOIN pg_attribute
        ON pg_attribute.attrelid = class_table.oid
            AND pg_depend.refobjsubid = pg_attribute.attnum
    INNER JOIN pg_namespace as table_namespace
        ON table_namespace.oid = class_table.relnamespace
    INNER JOIN pg_namespace AS sequence_namespace
        ON sequence_namespace.oid = class_sequence.relnamespace
ORDER BY sequence_namespace.nspname, class_sequence.relname;
"""))
                for stmt, in cur.all():
                    target_connection.execute(sqlalchemy.text(stmt))
                target_connection.commit()
        logging.info("Data migration finished")

    # Upgrade to the latest database revision
    flask_migrate.upgrade(directory=migrations.__path__[0])

    logging.info("Database initialised successfully!")


APP = create_app(imprint=APP.config['IMPRINT'], gdpr=APP.config['GDPR'])
CORS(APP, origins=APP.config.get(['CORS_ORIGINS'], ["*"]))
auth = HTTPBasicAuth()
with APP.app_context():
    current_app.extensions["basic_auth"] = auth


try:
    from mscolab_auth import mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mscolab_auth:
        allowed_users = [("mscolab", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None


# setup http auth
# for current test setup of test_server_auth_required we need the definition on module level
# so the import works regardless of when server was first loaded.
def authfunc(username, password):
    for u, p in mscolab_auth.allowed_users:
        if (u == username) and (p == hashlib.md5(password.encode('utf-8')).hexdigest()):
            return True
    return False


def verify_pw(username, password):
    if request.authorization:
        _auth = request.authorization
        username = _auth.username
        password = _auth.password
    return authfunc(username, password)


if APP.__dict__.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    auth.verify_password(verify_pw)


def _initialize_managers(app):
    sockio, cm, fm = _setup_managers(app)
    app.extensions['cm'] = cm
    app.extensions['sockio'] = sockio
    app.extensions['fm'] = fm
    # initializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    # db.init_app(app)
    return app, sockio, cm, fm


_app, sockio, cm, fm = _initialize_managers(APP)


def check_login(emailid, password):
    try:
        user = User.query.filter_by(emailid=str(emailid)).first()
    except sqlalchemy.exc.OperationalError as ex:
        logging.debug("Problem in the database (%ex), likely version client different", ex)
        return False
    if user is not None:
        if APP.config['MAIL_ENABLED']:
            if user.confirmed:
                if user.verify_password(password):
                    return user
        else:
            if user.verify_password(password):
                return user
    return False


def get_mail():
    return current_app.extensions['mail']


# 413: Payload Too Large
@APP.errorhandler(413)
def error413(error):
    upload_limit = APP.config['MAX_CONTENT_LENGTH'] / 1024 / 1024
    return jsonify({"success": False, "message": f"File size too large. Upload limit is {upload_limit}MB"}), 413


def start_server(app, sockio, cm, fm, port=8083):
    with app.app_context():
        _handle_db_upgrade()
    Mail(app)
    sockio.run(app, port=port, debug=APP.config['DEBUG'])


def main():
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)


if __name__ == '__main__':
    main()
