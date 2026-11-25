"""Course-specific rules: the database name, the expected table count, the load
sequence and how the delete-rule results are judged."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pymysql

from .db import base_table_names
from .paths import load_files
from .runner import ResultSet, run_script

COURSE_SCHEMA = "seattle_marketplace"
EXPECTED_TABLE_COUNT = 23

# MySQL error numbers for "the object already exists" (ER_TABLE_EXISTS_ERROR, ER_DB_CREATE_EXISTS).
ALREADY_EXISTS_ERRNOS = frozenset({1050, 1007})
RESET_HINT = (
    "The database already has objects from an earlier load. Reset it first: run "
    "./mysql/reset.sh for the Docker sandbox, or DROP DATABASE seattle_marketplace on your "
    "server. Then run ie6700 load again."
)

_RULE_COLUMNS = ("seq", "rule_name", "expected", "actual", "leftover", "result")
_TOTAL_COLUMNS = ("passed", "failed")


class UnexpectedOutputError(Exception):
    """delete_rules.sql returned result sets in a shape the CLI does not know."""


@dataclass(frozen=True)
class DeleteRuleOutcome:
    rule_count: int
    passed: int
    failed: int
    failing_rules: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.rule_count > 0 and not self.failing_rules and self.failed == 0


def load_course(
    conn: pymysql.connections.Connection,
    *,
    on_file_start: Callable[[str], None] | None = None,
    on_file_done: Callable[[str], None] | None = None,
) -> None:
    """Run the load sequence in order. Raises SqlScriptError at the first failing statement."""
    for name, path in load_files():
        if on_file_start:
            on_file_start(name)
        run_script(conn, path)
        if on_file_done:
            on_file_done(name)


def course_table_count(conn: pymysql.connections.Connection) -> int:
    return len(base_table_names(conn, COURSE_SCHEMA))


def evaluate_delete_rules(results: Sequence[ResultSet]) -> DeleteRuleOutcome:
    """Judge the output of delete_rules.sql: the rule table, then the totals.

    The SQL itself always ends with status 0, so the verdict is derived here: a
    rule fails when its result is not PASS, and the run fails when the failed
    total is not 0.
    """
    if len(results) < 2:
        raise UnexpectedOutputError(
            f"delete_rules.sql returned {len(results)} result set(s); expected the rule table "
            "and the totals."
        )
    rules, totals = results[0], results[1]
    if rules.columns != _RULE_COLUMNS:
        raise UnexpectedOutputError(
            f"The rule table has columns {', '.join(rules.columns)}; expected "
            f"{', '.join(_RULE_COLUMNS)}."
        )
    if totals.columns != _TOTAL_COLUMNS or len(totals.rows) != 1:
        raise UnexpectedOutputError("The totals row of delete_rules.sql has an unexpected shape.")

    result_index = _RULE_COLUMNS.index("result")
    name_index = _RULE_COLUMNS.index("rule_name")
    failing = [str(row[name_index]) for row in rules.rows if row[result_index] != "PASS"]
    passed_total, failed_total = totals.rows[0]
    return DeleteRuleOutcome(
        rule_count=len(rules.rows),
        passed=int(passed_total or 0),
        failed=int(failed_total or 0),
        failing_rules=failing,
    )
