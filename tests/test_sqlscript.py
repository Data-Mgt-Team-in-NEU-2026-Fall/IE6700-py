import json
from pathlib import Path

import pytest

from ie6700.paths import LOAD_SEQUENCE, REPO_ROOT, sql_dir
from ie6700.sqlscript import SqlSplitError, split_script

EXPECTED = Path(__file__).resolve().parent / "expected" / "statement_counts.json"
COURSE_FILES = [*LOAD_SEQUENCE, "queries.sql", "delete_rules.sql"]


def sqls(text: str) -> list[str]:
    return [statement.sql for statement in split_script(text)]


def test_plain_statements_are_split_on_semicolons():
    assert sqls("SELECT 1;\nSELECT 2;") == ["SELECT 1", "SELECT 2"]


def test_last_statement_without_semicolon_is_kept():
    assert sqls("SELECT 1;\nSELECT 2") == ["SELECT 1", "SELECT 2"]


def test_procedure_with_inner_semicolons_is_one_statement_under_delimiter():
    script = (
        "DELIMITER //\n"
        "CREATE PROCEDURE p(IN x INT)\n"
        "BEGIN\n"
        "  SET @a = x;\n"
        "  SELECT @a;\n"
        "END//\n"
        "DELIMITER ;\n"
        "CALL p(1);\n"
    )
    statements = split_script(script)
    assert len(statements) == 2
    assert statements[0].sql.startswith("CREATE PROCEDURE p(IN x INT)")
    assert statements[0].sql.endswith("END")
    assert "SET @a = x;" in statements[0].sql
    assert statements[0].line == 2
    assert statements[1].sql == "CALL p(1)"
    assert statements[1].line == 8


def test_delimiter_directive_is_never_part_of_a_statement():
    for statement in split_script("DELIMITER //\nSELECT 1//\nDELIMITER ;\nSELECT 2;"):
        assert "DELIMITER" not in statement.sql.upper()


def test_semicolon_in_string_does_not_split():
    assert sqls("SELECT 'a;b';") == ["SELECT 'a;b'"]


def test_escaped_and_doubled_quotes_do_not_end_the_string():
    assert sqls(r"SELECT 'it\'s; fine', 'it''s; fine';") == [r"SELECT 'it\'s; fine', 'it''s; fine'"]


def test_double_quotes_and_backticks_protect_the_delimiter():
    assert sqls('SELECT "a;b", `c;d` FROM `t;x`;') == ['SELECT "a;b", `c;d` FROM `t;x`']


def test_semicolon_in_line_comment_does_not_split():
    statements = split_script("SELECT 1 -- a; b\n;\nSELECT 2;")
    assert [s.sql for s in statements] == ["SELECT 1 -- a; b", "SELECT 2"]


def test_semicolon_in_hash_and_block_comments_does_not_split():
    assert sqls("SELECT 1 # x; y\n;") == ["SELECT 1 # x; y"]
    assert sqls("SELECT /* a; b */ 1;") == ["SELECT /* a; b */ 1"]


def test_dash_dash_without_following_space_is_not_a_comment():
    # MySQL needs whitespace after "--" for a comment, so the semicolon still ends the statement.
    assert sqls("SELECT 1 --;\nSELECT 2;") == ["SELECT 1 --", "SELECT 2"]


def test_dash_dash_with_following_space_is_a_comment():
    # The semicolon inside the comment is text; only the final ";" ends the statement.
    assert sqls("SELECT 1 -- note;\n;") == ["SELECT 1 -- note;"]


def test_conditional_comments_are_passed_through_unchanged():
    statements = split_script("/*!50003 SET @x = 1 */;\nSELECT @x;")
    assert [s.sql for s in statements] == ["/*!50003 SET @x = 1 */", "SELECT @x"]


def test_crlf_gives_the_same_statements_as_lf():
    lf = "-- 1.1 first\nSELECT 'a\nb';\n-- 1.2 second\nSELECT 2;\n"
    crlf = lf.replace("\n", "\r\n")
    assert split_script(crlf) == split_script(lf)


def test_byte_order_mark_is_ignored():
    assert sqls("﻿SELECT 1;") == ["SELECT 1"]


def test_comment_only_chunks_are_dropped():
    script = "-- only a comment\n;\n/* block only */\n# hash only\n;;\n-- trailing comment\n"
    assert split_script(script) == []


def test_empty_statements_are_dropped():
    assert sqls(";;SELECT 1;;") == ["SELECT 1"]


def test_start_line_is_the_first_token_not_a_leading_comment():
    statements = split_script("\n\n-- heading\n\nSELECT 1;\n")
    assert statements[0].line == 5
    assert statements[0].sql == "SELECT 1"


def test_section_comment_applies_to_every_later_statement_until_the_next_section():
    script = (
        "-- 6. Changes (rolled back)\n"
        "-- 6.1 UC-3201 Publish an item\n"
        "START TRANSACTION;\n"
        "SELECT 1;\n"
        "-- 7. Reports\n"
        "SELECT 2;\n"
    )
    statements = split_script(script)
    assert [s.section for s in statements] == [
        "6. Changes (rolled back)",
        "6. Changes (rolled back)",
        "7. Reports",
    ]
    assert statements[0].heading == "6.1 UC-3201 Publish an item"
    assert statements[1].heading is None


def test_numbered_heading_comment_is_kept():
    script = (
        "-- ============\n"
        "-- 1. Identity\n"
        "-- ============\n"
        "-- 1.1 UC-1101 Sign in with the campus e-mail\n"
        "SELECT 1;\n"
        "SELECT 2;\n"
        "-- A note without a number\n"
        "SELECT 3;\n"
    )
    statements = split_script(script)
    assert statements[0].heading == "1.1 UC-1101 Sign in with the campus e-mail"
    assert statements[1].heading is None
    assert statements[2].heading is None


def test_unterminated_quote_is_reported_with_its_line():
    with pytest.raises(SqlSplitError) as info:
        split_script("SELECT 1;\nSELECT 'oops;\n")
    assert info.value.line == 2
    assert "unterminated" in info.value.message


def test_unterminated_block_comment_is_reported():
    with pytest.raises(SqlSplitError, match="block comment"):
        split_script("SELECT 1 /* never closed;")


@pytest.mark.parametrize("name", COURSE_FILES)
def test_every_real_course_file_splits_cleanly(name: str):
    text = (sql_dir() / name).read_text(encoding="utf-8-sig")
    statements = split_script(text)
    assert statements, name
    for statement in statements:
        assert statement.sql.strip() == statement.sql
        assert statement.sql
        for line in statement.sql.splitlines():
            assert not line.strip().upper().startswith("DELIMITER"), (name, statement.line)


@pytest.mark.parametrize("name", COURSE_FILES)
def test_statement_count_matches_the_committed_count(name: str):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    actual = len(split_script((sql_dir() / name).read_text(encoding="utf-8-sig")))
    assert actual == expected[name], f"{name}: expected {expected[name]} statements, got {actual}"


def test_real_repository_root_contains_the_mysql_folder():
    assert (REPO_ROOT / "mysql" / "marketplace.sql").is_file()
