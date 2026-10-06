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
import secrets

import sqlalchemy as sa


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
