"""Expected results of the course SQL, checked against a loaded server.

The expectations live in tests/expected/ so a deliberate seed change shows up in a diff.
"""

import json
from pathlib import Path

from ie6700 import db
from ie6700.course import COURSE_SCHEMA, EXPECTED_TABLE_COUNT, evaluate_delete_rules
from ie6700.paths import delete_rules_path, queries_path
from ie6700.runner import run_script

EXPECTED_DIR = Path(__file__).resolve().parents[1] / "expected"


def read_expected(name: str):
    return json.loads((EXPECTED_DIR / name).read_text(encoding="utf-8"))


DELETE_RULE_COUNT = 27
HEALTH_COLUMNS = ("check", "violations")
QUERY_SECTIONS = {str(n) for n in range(1, 9)}


def test_course_schema_has_the_expected_number_of_base_tables(loaded_db, conn):
    names = db.base_table_names(conn, COURSE_SCHEMA)
    assert len(names) == EXPECTED_TABLE_COUNT, names


def test_row_counts_match_the_committed_expectation(loaded_db, conn):
    expected = read_expected("row_counts.json")["tables"]
    actual = dict(db.table_counts(conn, COURSE_SCHEMA))
    mismatches = [
        f"{table}: expected {expected.get(table)}, actual {actual.get(table)}"
        for table in sorted(set(expected) | set(actual))
        if expected.get(table) != actual.get(table)
    ]
    assert not mismatches, "Row counts differ from tests/expected/row_counts.json:\n" + "\n".join(mismatches)


def test_delete_rules_are_all_pass_with_no_failures(loaded_db, conn):
    outcome = evaluate_delete_rules(run_script(conn, delete_rules_path()))
    assert outcome.rule_count == DELETE_RULE_COUNT
    assert outcome.passed == DELETE_RULE_COUNT
    assert outcome.failed == 0
    assert outcome.failing_rules == []
    assert outcome.ok


def test_every_expected_health_check_is_present_with_zero_violations(loaded_db, conn):
    results = run_script(conn, queries_path())
    health = [r for r in results if r.columns == HEALTH_COLUMNS]
    assert len(health) == 1, "queries.sql should end with exactly one data-health result set"

    expected_names = read_expected("health_checks.json")["checks"]
    violations = {str(row[0]): int(row[1]) for row in health[0].rows}

    missing = [name for name in expected_names if name not in violations]
    assert not missing, f"Health checks missing from queries.sql section 8: {missing}"
    nonzero = {name: count for name, count in violations.items() if count != 0}
    assert not nonzero, f"Health checks with violations: {nonzero}"


def test_queries_file_runs_end_to_end_and_covers_every_section(loaded_db, conn):
    results = run_script(conn, queries_path())
    labels = [r.heading or r.section for r in results]
    sections = {label.split(" ")[0].split(".")[0] for label in labels if label}
    assert QUERY_SECTIONS <= sections, f"sections without results: {sorted(QUERY_SECTIONS - sections)}"
