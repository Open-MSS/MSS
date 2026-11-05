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
import logging
import secrets

import sqlalchemy as sa


class _ForeignKeyCheck:
    """whether sqlite_foreign_keys_off checks the foreign keys at its end"""
    def __init__(self):
        self.check = True


@contextlib.contextmanager
def sqlite_foreign_keys_off(connection):
    """
    Runs schema changes in one transaction of connection, on SQLite with the foreign keys switched off; commits it
    only if no row refers to a missing row

    The batch mode of alembic recreates tables on SQLite, which needs them off, see
    https://www.sqlite.org/lang_altertable.html#otheralter. The PRAGMA has no effect inside a transaction, so
    connection must have none open. Rows left referring to missing rows roll everything back and raise a
    RuntimeError, as PostgreSQL would refuse them; setting check of the yielded object to False skips that check.
    The transaction is begun here, alembic runs inside it and doesn't commit on its own.
    """
    state = _ForeignKeyCheck()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
    try:
        with connection.begin():
            yield state
            # checked inside the transaction: a violation rolls the changes back
            violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall() \
                if sqlite and state.check else []
            if violations:
                raise RuntimeError("Rows refer to missing rows (table, rowid, referred table, foreign key): "
                                   f"{violations}")
    finally:
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


@contextlib.contextmanager
def batch_alter_table(op, conn, table, **kwargs):
    """
    op.batch_alter_table that keeps AUTOINCREMENT of a table of AUTOINCREMENT_TABLES on SQLite

    alembic recreates the table from what SQLAlchemy reflects, and that doesn't include AUTOINCREMENT; the new table
    also counts on from its highest id, so the ids of deleted rows above it would be handed out again. Both are put
    back here.
    """
    keep = conn.dialect.name == "sqlite" and table in AUTOINCREMENT_TABLES and has_autoincrement_ids(conn, table)
    sequence = None
    if keep:
        kwargs["table_kwargs"] = dict(kwargs.get("table_kwargs", {}), sqlite_autoincrement=True)
        sequence = conn.execute(sa.text("SELECT seq FROM sqlite_sequence WHERE name = :table"),
                                {"table": table}).scalar()
    with op.batch_alter_table(table, schema=None, **kwargs) as batch_op:
        yield batch_op
    if sequence is not None:
        conn.execute(sa.text("UPDATE sqlite_sequence SET seq = :seq WHERE name = :table AND seq < :seq"),
                     {"seq": sequence, "table": table})


def has_column(conn, table, column):
    """True if table exists in the database of conn and has column"""
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names() and column in {c["name"] for c in inspector.get_columns(table)}


def add_token_nonce(op, conn):
    """
    Adds users.token_nonce, the random value of the login tokens of a user, every user gets their own

    op is an alembic Operations object for conn.
    """
    with batch_alter_table(op, conn, 'users') as batch_op:
        batch_op.add_column(sa.Column('token_nonce', sa.String(length=32), nullable=True))
    for (u_id,) in conn.execute(sa.text("SELECT id FROM users")).fetchall():
        conn.execute(sa.text("UPDATE users SET token_nonce = :nonce WHERE id = :id"),
                     {"nonce": secrets.token_hex(16), "id": u_id})
    with batch_alter_table(op, conn, 'users') as batch_op:
        batch_op.alter_column('token_nonce', existing_type=sa.String(length=32), nullable=False)


_MISSING_USER = "{column} IS NOT NULL AND {column} NOT IN (SELECT id FROM users)"
_MISSING_OPERATION = "op_id IS NOT NULL AND op_id NOT IN (SELECT id FROM operations)"

# The rows that refer to a deleted user or operation, as older versions left them behind, and how they are repaired,
# in this order: (table, column or None for the whole row, condition, log message). A column is set to NULL, the
# row stays: messages and changes of a deleted user, a reply to a deleted message. Any other such row is removed.
# The one place of these rules: the 12.0.0 migration, `mscolab db --repair_references`, the warning of a server start
# and the copy of an older database in app.initialise_db (KEPT_WITHOUT_REFERENCE) use them.
DANGLING_REFERENCES = (
    ("permissions", None, f"({_MISSING_USER.format(column='u_id')}) OR ({_MISSING_OPERATION})",
     "deleted the permissions %s of deleted users or operations"),
    # before the answered message goes; PostgreSQL checks the reference per statement. The inner SELECT is a table of
    # its own: MySQL doesn't update a table selected from in the same statement
    ("messages", "reply_id",
     "reply_id IS NOT NULL AND reply_id NOT IN (SELECT id FROM (SELECT id FROM messages WHERE op_id IS NULL "
     "OR op_id IN (SELECT id FROM operations)) AS kept_messages) "
     "AND (op_id IS NULL OR op_id IN (SELECT id FROM operations))",
     "removed the answered message from the replies %s, it is deleted or missing"),
    ("messages", None, _MISSING_OPERATION, "deleted the chat messages %s of deleted operations"),
    ("changes", None, _MISSING_OPERATION, "deleted the flight track changes %s of deleted operations"),
    # the rows of deleted operations are gone already
    ("messages", "u_id", _MISSING_USER.format(column="u_id"),
     "kept the chat messages %s of deleted users without their user"),
    ("changes", "u_id", _MISSING_USER.format(column="u_id"),
     "kept the flight track changes %s of deleted users without their user"),
)
KEPT_WITHOUT_REFERENCE = tuple((table, column) for table, column, _, _ in DANGLING_REFERENCES if column is not None)


def has_dangling_references(conn):
    """
    True if a row refers to a deleted user or operation, see DANGLING_REFERENCES; stops at the first one

    Always False on PostgreSQL, its foreign keys refuse such rows.
    """
    if conn.dialect.name == "postgresql":
        return False
    return any(conn.execute(sa.text(f"SELECT 1 FROM {table} WHERE {condition} LIMIT 1")).first() is not None
               for table, _, condition, _ in DANGLING_REFERENCES)


def remove_dangling_references(conn):
    """
    Repairs the rows that refer to a deleted user or operation, see DANGLING_REFERENCES; returns how many rows
    were changed

    Before 12.0.0 a deleted user left its chat messages and flight track changes behind, still referring to it, and
    a deleted operation could leave its rows behind. SQLite didn't check this, PostgreSQL refuses it. The messages
    and changes of a deleted user stay, without the user, as when a user is deleted now; the rows of a deleted
    operation are removed. It deletes rows, so it runs only in the 12.0.0 migration and by
    `mscolab db --repair_references`, never on a server start. Logs the ids of every row it changes; the statements
    use the conditions, not the ids, so any number of rows works.
    """
    changed = 0
    for table, column, condition, message in DANGLING_REFERENCES:
        ids = [row.id for row in conn.execute(sa.text(f"SELECT id FROM {table} WHERE {condition}"))]
        if not ids:
            continue
        logging.warning("Repairing the database: " + message, ids)
        if column is None:
            conn.execute(sa.text(f"DELETE FROM {table} WHERE {condition}"))
        else:
            conn.execute(sa.text(f"UPDATE {table} SET {column} = NULL WHERE {condition}"))
        changed += len(ids)
    return changed


def hand_over_operations_without_creator(conn):
    """
    Makes the admin who is a member longest the creator of each operation without creator, as when a creator is
    deleted now (User.prepare_deletion); returns the operations that keep none

    Before 12.0.0 deleting a creator deleted the creator permission too, and a {category}Group operation could
    downgrade or remove the creator. An operation without an admin keeps no creator, one without members stays: a
    migration doesn't delete operations and their files. Both are logged.
    """
    without_creator = []
    for (op_id,) in conn.execute(sa.text(
            "SELECT id FROM operations WHERE id NOT IN "
            "(SELECT op_id FROM permissions WHERE access_level = 'creator' AND op_id IS NOT NULL) ORDER BY id")):
        admin = conn.execute(sa.text("SELECT id, u_id FROM permissions WHERE op_id = :op_id "
                                     "AND access_level = 'admin' ORDER BY id LIMIT 1"), {"op_id": op_id}).first()
        if admin is None:
            logging.warning("operation %s has no creator and no admin, only a creator can delete it", op_id)
            without_creator.append(op_id)
            continue
        conn.execute(sa.text("UPDATE permissions SET access_level = 'creator' WHERE id = :id"), {"id": admin.id})
        logging.warning("operation %s had no creator, its admin, the user %s, is its creator now", op_id, admin.u_id)
    return without_creator


# the tables whose ids SQLite must never hand out again: a token or socket of a deleted user, or the attachments of
# a deleted operation (stored by operation id), would belong to the new row
AUTOINCREMENT_TABLES = ("users", "operations")


def has_autoincrement_ids(conn, table):
    """True unless the database is SQLite and table reuses the ids of deleted rows"""
    if conn.dialect.name != "sqlite":
        return True
    sql = conn.execute(sa.text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = :table"),
                       {"table": table}).scalar()
    return sql is None or "AUTOINCREMENT" in sql.upper()


def use_autoincrement_ids(op, conn):
    """
    Lets SQLite never hand out the id of a deleted row of AUTOINCREMENT_TABLES again, as PostgreSQL never does

    Without AUTOINCREMENT, SQLite gives a new row the highest id + 1, so a new user or operation can get the id of
    the last deleted one. op is an alembic Operations object for conn. Returns the tables it changed.
    """
    changed = []
    for table in AUTOINCREMENT_TABLES:
        if not has_autoincrement_ids(conn, table):
            with op.batch_alter_table(table, schema=None, recreate='always',
                                      table_kwargs={'sqlite_autoincrement': True}):
                pass
            changed.append(table)
    return changed


def add_fullname(op, conn):
    """
    Adds users.fullname, if it is missing

    11.0.0 added it to the migration of 10.0.0 after that was released, so a database created by 10.x and upgraded
    later misses it. op is an alembic Operations object for conn.
    """
    if not has_column(conn, 'users', 'fullname'):
        with batch_alter_table(op, conn, 'users') as batch_op:
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
    inspector = sa.inspect(conn)
    for table in inspector.get_table_names():
        if "id" not in {column["name"] for column in inspector.get_columns(table)}:
            continue
        sequence = conn.execute(sa.text("SELECT pg_get_serial_sequence(:table, 'id')"), {"table": table}).scalar()
        if sequence is None:
            continue
        highest = conn.execute(sa.text(f'SELECT MAX(id) FROM "{table}"')).scalar()
        if highest is None:
            # an empty table, a sequence not used yet would otherwise start at 2
            continue
        # sequence is the quoted, schema qualified name from the catalog. Only a sequence behind is set, in one
        # statement: the server may insert at the same time, a sequence read before would then be moved back
        # last_value is the next value as long as the sequence wasn't used
        conn.execute(sa.text(f"SELECT setval(:sequence, :highest) WHERE :highest > (SELECT CASE WHEN is_called "
                             f"THEN last_value ELSE last_value - 1 END FROM {sequence})"),
                     {"sequence": sequence, "highest": highest})
