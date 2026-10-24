# -*- coding: utf-8 -*-
"""

    tests.database
    ~~~~~~~~~~~~~~

    The databases of the MSColab test servers: SQLite files by default, PostgreSQL databases
    when MSCOLAB_TEST_POSTGRES_URL names a PostgreSQL server, e.g.

        MSCOLAB_TEST_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432 pixi run -e dev test-mscolab

    The production servers run on PostgreSQL, which behaves differently from SQLite, e.g. it
    locks tables for schema changes and checks foreign keys per statement. Every test app and
    every test process gets a database of its own, which is dropped again at the end.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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
import logging
import os
import uuid

POSTGRES_URL = os.environ.get("MSCOLAB_TEST_POSTGRES_URL", "")

# databases created by this process, dropped by drop_databases()
_created = []
# the database of the test server of this process, see server_database_uri()
_server_database_uri = None


def _url(database):
    """the URL of MSCOLAB_TEST_POSTGRES_URL with another database, its options (e.g. sslmode) are kept"""
    import sqlalchemy
    return sqlalchemy.engine.make_url(POSTGRES_URL).set(database=database)


def _server_engine():
    import sqlalchemy
    # CREATE and DROP DATABASE can't run in a transaction
    return sqlalchemy.create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")


def database_uri(sqlite_file, prefix="mscolab"):
    """
    SQLAlchemy URI of a new, empty test database.

    <sqlite_file> is the database without MSCOLAB_TEST_POSTGRES_URL; with it, a PostgreSQL
    database with a unique name is created.
    """
    if not POSTGRES_URL:
        return f"sqlite:///{sqlite_file}"
    import sqlalchemy
    name = f"mss_test_{prefix}_{uuid.uuid4().hex[:12]}"
    engine = _server_engine()
    try:
        with engine.connect() as connection:
            # UTF8 also where the server's default is SQL_ASCII, e.g. after initdb with the C locale
            connection.execute(sqlalchemy.text(
                f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0'))
    finally:
        engine.dispose()
    _created.append(name)
    return _url(name).render_as_string(hide_password=False)


def server_database_uri(sqlite_file):
    """
    database_uri() of the test server of this process, the same on every call

    The generated mscolab_settings.py is executed again before every test, the server keeps
    the database of its first execution.
    """
    global _server_database_uri
    if _server_database_uri is None:
        _server_database_uri = database_uri(sqlite_file, prefix="server")
    return _server_database_uri


def drop_database(uri):
    """drops a PostgreSQL database of database_uri(), also when connections to it are still open"""
    if not POSTGRES_URL:
        return
    import sqlalchemy
    name = sqlalchemy.engine.make_url(uri).database
    if name not in _created:
        return
    engine = _server_engine()
    try:
        with engine.connect() as connection:
            connection.execute(sqlalchemy.text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        engine.dispose()
    _created.remove(name)


def drop_databases():
    """drops the PostgreSQL databases this process created and didn't drop yet, an error is only logged"""
    for name in list(_created):
        try:
            drop_database(_url(name).render_as_string(hide_password=False))
        except Exception as ex:  # the end of the test session must not fail because of it
            logging.error("Could not drop the test database %s: %s", name, ex)
