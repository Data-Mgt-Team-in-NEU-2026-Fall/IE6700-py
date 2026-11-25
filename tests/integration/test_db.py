"""Connection and catalogue checks against a live server (skipped without DATABASE_URL)."""

from ie6700 import db
from ie6700.course import COURSE_SCHEMA


def test_connects_to_a_mysql_8_server(db_settings):
    conn = db.connect(db_settings)
    try:
        version = db.server_version(conn)
        db.check_server_version(version)
        assert version
    finally:
        conn.close()


def test_table_counts_are_exact_for_the_course_schema(loaded_db, conn):
    counts = db.table_counts(conn, COURSE_SCHEMA)
    assert len(counts) == 23
    for table, count in counts:
        assert isinstance(count, int), table
        assert count >= 0, table
