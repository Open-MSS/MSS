# -*- coding: utf-8 -*-
"""

    mslib.mscolab.app
    ~~~~~~~~~~~~~~~~~

    app module of mscolab

    This file is part of MSS.

    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import datetime
import os
import logging
import sys
from pathlib import Path

import flask_migrate
import sqlalchemy
from flask_mail import Mail

from flask_migrate import Migrate
from flask import Flask

import mslib

from flask import url_for
from flask_sqlalchemy import SQLAlchemy

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab import migrations
from mslib.utils import prefix_route, release_info
from mslib.utils.file_exists import file_exists
from xstatic.main import XStatic


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_BLUEPRINTS_DIR = os.path.join(DOCS_SERVER_PATH, 'blueprints')
DOCS_BLUEPRINTS_DOCS_DIR = os.path.join(DOCS_BLUEPRINTS_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'templates')
DOCS_STATIC_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')


message, update = release_info.check_for_new_release()
if update:
    logging.warning(message)


# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_TEMPLATES_DIR))
APP.jinja_env.globals.setdefault("imprint", "")
APP.jinja_env.globals.setdefault("gdpr", "")
APP.config.from_object(mscolab_settings)
# Expose docs path for callers/tests and make it part of Flask config for consistency.
APP.config['DOCS_SERVER_PATH'] = DOCS_SERVER_PATH
APP.route = prefix_route(APP.route, SCRIPT_NAME)


def _xstatic(name):
    mod_names = [
        'jquery', 'bootstrap',
    ]
    pkg = __import__('xstatic.pkg', fromlist=mod_names)
    serve_files = {}

    for mod_name in mod_names:
        mod = getattr(pkg, mod_name)
        # ToDo protocol should become configurable
        xs = XStatic(mod, root_url='/static', provider='local', protocol='http')
        serve_files[xs.name] = xs.base_dir
    try:
        return serve_files[name]
    except KeyError:
        return None


# Keep backward compatibility with callers/tests expecting an app attribute.
APP.xstatic = _xstatic


def create_files():
    Path(APP.config['OPERATIONS_DATA']).mkdir(parents=True, exist_ok=True)
    Path(APP.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(APP.config['SSO_DIR']).mkdir(parents=True, exist_ok=True)


def _handle_db_upgrade():
    from mslib.mscolab.models import db

    # Remove any stale session state before inspecting the schema; a lingering
    # open transaction (e.g. from a previous iteration in test_upgrade_from)
    # can cause the inspector to see a stale/empty table list on Windows.
    db.session.remove()
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
        # Copy over the existing data.
        # Use db.engine.url (the resolved absolute URL) rather than
        # APP.config['SQLALCHEMY_DATABASE_URI'], which may be a relative SQLite
        # path that Flask-SQLAlchemy expands via instance_path — plain
        # sqlalchemy.create_engine would resolve it against CWD instead.
        target_engine = sqlalchemy.create_engine(str(db.engine.url))
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
        # Dispose the temporary copy engine so it doesn't hold SQLite
        # connections across subsequent _handle_db_upgrade() iterations.
        target_engine.dispose()
        source_engine.dispose()

    # Upgrade to the latest database revision
    flask_migrate.upgrade(directory=migrations.__path__[0])

    logging.info("Database initialised successfully!")


def create_app(imprint=None, gdpr=None):
    imprint_file = imprint
    gdpr_file = gdpr
    APP.mail = Mail(APP)

    with APP.app_context():
        _handle_db_upgrade()

    APP.jinja_env.globals.update(file_exists=file_exists)
    APP.jinja_env.globals["imprint"] = imprint_file or ""
    APP.jinja_env.globals["gdpr"] = gdpr_file or ""
    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    from mslib.mscolab.blueprints.auth import AUTH_BP
    from mslib.mscolab.blueprints.chat import CHAT_BP
    from mslib.mscolab.blueprints.operation import OPERATION_BP
    from mslib.mscolab.blueprints.user import USER_BP
    from mslib.mscolab.blueprints.docs import DOCS_BP

    if AUTH_BP.name not in APP.blueprints:
        APP.register_blueprint(AUTH_BP)
    if CHAT_BP.name not in APP.blueprints:
        APP.register_blueprint(CHAT_BP)
    if USER_BP.name not in APP.blueprints:
        APP.register_blueprint(USER_BP)
    if OPERATION_BP.name not in APP.blueprints:
        APP.register_blueprint(OPERATION_BP)
    if DOCS_BP.name not in APP.blueprints:
        APP.register_blueprint(DOCS_BP)

    return APP


db = SQLAlchemy(
    metadata=sqlalchemy.MetaData(
        naming_convention={
            # For reference: https://alembic.sqlalchemy.org/en/latest/naming.html#the-importance-of-naming-constraints
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    ),
)
db.init_app(APP)

migrate = Migrate(render_as_batch=True, user_module_prefix="cu.")
migrate.init_app(APP, db)


def get_topmenu():
    menu = [
        (url_for('docs.index'), 'Mission Support System',
         ((url_for('docs.about'), 'About'),
          (url_for('docs.install'), 'Install'),
          (url_for('docs.help'), 'Help'),
          )),
    ]
    return menu
