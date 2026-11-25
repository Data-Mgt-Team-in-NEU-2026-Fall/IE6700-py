from pathlib import Path

import pytest

from ie6700.paths import (
    DELETE_RULES_FILE,
    LOAD_SEQUENCE,
    QUERIES_FILE,
    REPO_ROOT,
    SQL_DIR_ENV,
    SqlFilesError,
    load_files,
    queries_path,
    delete_rules_path,
    script_path,
    sql_dir,
)


def test_default_sql_dir_is_the_repository_mysql_folder():
    assert sql_dir({}) == REPO_ROOT / "mysql"
    assert sql_dir({}).is_dir()


def test_override_points_at_another_folder(tmp_path: Path):
    assert sql_dir({SQL_DIR_ENV: str(tmp_path)}) == tmp_path


def test_blank_override_falls_back_to_default():
    assert sql_dir({SQL_DIR_ENV: "   "}) == REPO_ROOT / "mysql"


def test_missing_directory_gives_a_clear_message(tmp_path: Path):
    missing = tmp_path / "nowhere"
    with pytest.raises(SqlFilesError) as info:
        sql_dir({SQL_DIR_ENV: str(missing)})
    message = str(info.value)
    assert "SQL directory not found" in message
    assert str(missing) in message
    assert SQL_DIR_ENV in message


def test_missing_file_in_override_is_reported(tmp_path: Path):
    with pytest.raises(SqlFilesError, match="Missing SQL file"):
        script_path(QUERIES_FILE, {SQL_DIR_ENV: str(tmp_path)})


def test_load_sequence_is_the_four_course_files_in_order():
    assert LOAD_SEQUENCE == (
        "marketplace.sql",
        "seed/01_identity.sql",
        "seed/02_marketplace.sql",
        "seed/03_messaging_reviews_reports.sql",
    )


def test_all_course_files_resolve_to_existing_files():
    names = [name for name, _ in load_files({})]
    assert names == list(LOAD_SEQUENCE)
    for _, path in load_files({}):
        assert path.is_file(), path
    assert queries_path({}).is_file()
    assert delete_rules_path({}).is_file()
    assert queries_path({}).name == QUERIES_FILE
    assert delete_rules_path({}).name == DELETE_RULES_FILE
