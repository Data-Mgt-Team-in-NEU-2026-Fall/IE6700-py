"""Runner behaviour against a live server, using a scratch database that is dropped afterwards."""

from pathlib import Path

import pytest

from ie6700 import db
from ie6700.runner import SqlScriptError, run_script

SCRATCH = "ie6700_runner_check"

PREFIX = f"""-- Runner check script
DROP DATABASE IF EXISTS {SCRATCH};
CREATE DATABASE {SCRATCH};
USE {SCRATCH};
SET @x = 41;
SELECT @x + 1 AS answer;
DELIMITER //
CREATE PROCEDURE two_sets()
BEGIN
  SELECT 'first' AS label;
  SELECT 'second' AS label;
END//
DELIMITER ;
CALL two_sets();
"""


def _line_of(text: str, needle: str) -> int:
    for number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return number
    raise AssertionError(needle)


@pytest.fixture
def scratch_conn(db_settings, tmp_path):
    conn = db.connect(db_settings)
    try:
        yield conn
    finally:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {SCRATCH}")
        conn.close()


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "script.sql"
    path.write_text(text, encoding="utf-8")
    return path


def test_result_sets_are_captured_in_order_with_their_lines(scratch_conn, tmp_path):
    text = PREFIX
    path = _write(tmp_path, text)

    results = run_script(scratch_conn, path)

    assert [r.columns for r in results] == [("answer",), ("label",), ("label",)]
    assert results[0].rows == [(42,)]
    assert results[1].rows == [("first",)]
    assert results[2].rows == [("second",)]
    assert results[0].line == _line_of(text, "SELECT @x + 1")
    assert results[1].line == results[2].line == _line_of(text, "CALL two_sets")
    assert all(r.source == str(path) for r in results)


def test_error_stops_the_run_and_reports_file_line_and_message(scratch_conn, tmp_path):
    bad = "SELECT * FROM no_such_table;"
    text = PREFIX + bad + "\nCREATE TABLE should_not_exist (id INT);\n"
    path = _write(tmp_path, text)

    with pytest.raises(SqlScriptError) as info:
        run_script(scratch_conn, path)

    error = info.value
    assert error.source == str(path)
    assert error.line == _line_of(text, bad)
    assert error.errno == 1146  # ER_NO_SUCH_TABLE
    assert "no_such_table" in error.message
    assert error.preview == bad.rstrip(";")  # the statement text, without its delimiter
    assert str(path) in str(error)
    assert f":{error.line}:" in str(error)

    # The statement after the failing one was not run.
    with scratch_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'should_not_exist'",
            (SCRATCH,),
        )
        (count,) = cur.fetchone()
    assert count == 0
