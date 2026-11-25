"""Shared fixtures.

Integration tests need a MySQL 8.x server named by DATABASE_URL (in the
environment or in a .env file). Without one they are skipped, not failed.
"""

from __future__ import annotations

import pytest

from ie6700 import db
from ie6700.config import ConfigError, Settings, load_settings
from ie6700.course import COURSE_SCHEMA, EXPECTED_TABLE_COUNT, RESET_HINT, course_table_count, load_course


@pytest.fixture(scope="session")
def db_settings() -> Settings:
    try:
        return load_settings()
    except ConfigError as exc:
        pytest.skip(f"no database configured: {exc}")


@pytest.fixture(scope="session")
def loaded_db(db_settings: Settings) -> Settings:
    """Make sure the course database is loaded once for the session.

    An empty server (or no course database yet) is loaded from the SQL files.
    A database that already has the 23 tables is used as it is, so a
    `ie6700 load` run before pytest does not clash. Any other state fails
    with the reset hint.
    """
    conn = db.connect(db_settings)
    try:
        db.check_server_version(db.server_version(conn))
        if course_table_count(conn) == 0:
            load_course(conn)
        count = course_table_count(conn)
    finally:
        conn.close()
    if count != EXPECTED_TABLE_COUNT:
        pytest.fail(
            f"{COURSE_SCHEMA} has {count} base tables; expected {EXPECTED_TABLE_COUNT}. {RESET_HINT}"
        )
    return db_settings


@pytest.fixture
def conn(loaded_db: Settings):
    connection = db.connect(loaded_db)
    try:
        yield connection
    finally:
        connection.close()
