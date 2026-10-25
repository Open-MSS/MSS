# -*- coding: utf-8 -*-
"""

    mslib.mscolab.migrations.schema_repair
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Schema changes of the 12.0.0 migration that a database can miss.

    All changes of a major release go into its one migration (docs/development.rst). A development
    database that already ran an earlier state of that migration is stamped with its revision, so
    alembic doesn't run the migration again and the later added changes are missing. They are added
    by the migration itself, and by :func:`mslib.mscolab.app.repair_schema` for such databases.

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
import contextlib
import secrets

import sqlalchemy as sa


class _ForeignKeyCheck:
    """whether sqlite_foreign_keys_off checks the foreign keys at its end"""
    def __init__(self):
        self.check = True


@contextlib.contextmanager
def sqlite_foreign_keys_off(connection):
    """
    Switches the foreign keys of an SQLite connection off for schema changes, checks them afterwards

    The batch mode of alembic recreates tables on SQLite, which needs them off, see
    https://www.sqlite.org/lang_altertable.html#otheralter. The PRAGMA has no effect inside a transaction, so
    connection must have none open. Rows left referring to missing rows raise a RuntimeError, PostgreSQL would
    refuse them; setting check of the yielded object to False skips that. Other databases are left as they are.
    """
    state = _ForeignKeyCheck()
    if connection.dialect.name != "sqlite":
        yield state
        return
    connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
    connection.commit()
    violations = []
    try:
        yield state
        connection.commit()
        if state.check:
            violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.rollback()
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
    if violations:
        raise RuntimeError(f"Rows refer to missing rows (table, rowid, referred table, foreign key): {violations}")


def has_column(conn, table, column):
    """True if table exists in the database of conn and has column"""
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names() and column in {c["name"] for c in inspector.get_columns(table)}


def add_token_nonce(op, conn):
    """
    Adds users.token_nonce, the random value of the login tokens of a user, every user gets their own

    op is an alembic Operations object for conn.
    """
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_nonce', sa.String(length=32), nullable=True))
    for (u_id,) in conn.execute(sa.text("SELECT id FROM users")).fetchall():
        conn.execute(sa.text("UPDATE users SET token_nonce = :nonce WHERE id = :id"),
                     {"nonce": secrets.token_hex(16), "id": u_id})
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('token_nonce', existing_type=sa.String(length=32), nullable=False)


def remove_dangling_references(conn):
    """
    Repairs rows that refer to a deleted user or operation, returns how many rows were changed

    Before 12.0.0 a deleted user left its chat messages and flight track changes behind, still referring to it, and
    a deleted operation could leave its rows behind. SQLite didn't check this, PostgreSQL refuses it. The messages
    and changes of a deleted user stay, without the user, as when a user is deleted now; the rows of a deleted
    operation are removed.
    """
    changed = conn.execute(sa.text(
        "DELETE FROM permissions WHERE u_id NOT IN (SELECT id FROM users) "
        "OR op_id NOT IN (SELECT id FROM operations)")).rowcount
    # a reply to a message that goes stays without it; PostgreSQL checks this per statement, so before the message
    # is deleted (the ids first: MySQL doesn't update a table selected from in the same statement)
    removed_ids = [row.id for row in conn.execute(sa.text(
        "SELECT id FROM messages WHERE op_id NOT IN (SELECT id FROM operations)"))]
    if removed_ids:
        changed += conn.execute(sa.text("UPDATE messages SET reply_id = NULL WHERE reply_id IN :ids")
                                .bindparams(sa.bindparam("ids", expanding=True)), {"ids": removed_ids}).rowcount
    for statement in (
            "DELETE FROM messages WHERE op_id NOT IN (SELECT id FROM operations)",
            "DELETE FROM changes WHERE op_id NOT IN (SELECT id FROM operations)",
            "UPDATE messages SET u_id = NULL WHERE u_id IS NOT NULL AND u_id NOT IN (SELECT id FROM users)",
            "UPDATE changes SET u_id = NULL WHERE u_id IS NOT NULL AND u_id NOT IN (SELECT id FROM users)"):
        changed += conn.execute(sa.text(statement)).rowcount
    # replies to messages that were already missing
    orphaned_replies = [row.id for row in conn.execute(sa.text(
        "SELECT reply.id FROM messages reply LEFT JOIN messages answered ON reply.reply_id = answered.id "
        "WHERE reply.reply_id IS NOT NULL AND answered.id IS NULL"))]
    if orphaned_replies:
        changed += conn.execute(sa.text("UPDATE messages SET reply_id = NULL WHERE id IN :ids")
                                .bindparams(sa.bindparam("ids", expanding=True)), {"ids": orphaned_replies}).rowcount
    return changed


def has_autoincrement_user_ids(conn):
    """True unless the database is SQLite and its table users reuses the ids of deleted users"""
    if conn.dialect.name != "sqlite":
        return True
    sql = conn.execute(sa.text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'")).scalar()
    return sql is None or "AUTOINCREMENT" in sql.upper()


def use_autoincrement_user_ids(op, conn):
    """
    Lets SQLite never hand out the id of a deleted user again, as PostgreSQL never does

    Without AUTOINCREMENT, SQLite gives a new row the highest id + 1, so a new user can get the id of the last
    deleted one. op is an alembic Operations object for conn.
    """
    if not has_autoincrement_user_ids(conn):
        with op.batch_alter_table('users', schema=None, recreate='always',
                                  table_kwargs={'sqlite_autoincrement': True}):
            pass


def add_fullname(op, conn):
    """
    Adds users.fullname, if it is missing

    11.0.0 added it to the migration of 10.0.0 after that was released, so a database created by 10.x and upgraded
    later misses it. op is an alembic Operations object for conn.
    """
    if not has_column(conn, 'users', 'fullname'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('fullname', sa.String(length=255), nullable=True))


def fix_postgresql_sequences(conn):
    """
    Moves the id sequences of a PostgreSQL database behind the highest id of their table, never back

    Rows inserted with explicit ids, by the seed or the copy of an older database, leave a sequence behind, so the
    next new row would get an id that exists. Never back: ids of deleted rows are not handed out again. Other
    databases are left as they are.
    """
    if conn.dialect.name != "postgresql":
        return
    for table in sa.inspect(conn).get_table_names():
        if "id" not in {column["name"] for column in sa.inspect(conn).get_columns(table)}:
            continue
        sequence = conn.execute(sa.text("SELECT pg_get_serial_sequence(:table, 'id')"), {"table": table}).scalar()
        if sequence is None:
            continue
        highest = conn.execute(sa.text(f'SELECT MAX(id) FROM "{table}"')).scalar()
        if highest is None:
            # an empty table, a sequence not used yet would otherwise start at 2
            continue
        # sequence is the quoted, schema qualified name from the catalog
        conn.execute(sa.text(f"SELECT setval(:sequence, GREATEST(:highest, (SELECT last_value FROM {sequence})))"),
                     {"sequence": sequence, "highest": highest})
