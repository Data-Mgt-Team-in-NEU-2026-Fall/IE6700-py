import pytest

from ie6700.course import UnexpectedOutputError, evaluate_delete_rules
from ie6700.runner import ResultSet

RULE_COLUMNS = ("seq", "rule_name", "expected", "actual", "leftover", "result")


def _rules(*results: str) -> ResultSet:
    rows = [
        (index + 1, f"rule {index + 1}", "blocked", "blocked", None, result)
        for index, result in enumerate(results)
    ]
    return ResultSet(columns=RULE_COLUMNS, rows=rows)


def _totals(passed: int, failed: int) -> ResultSet:
    return ResultSet(columns=("passed", "failed"), rows=[(passed, failed)])


def test_all_pass_is_ok():
    outcome = evaluate_delete_rules([_rules("PASS", "PASS"), _totals(2, 0)])
    assert outcome.ok
    assert outcome.rule_count == 2
    assert outcome.passed == 2
    assert outcome.failed == 0
    assert outcome.failing_rules == []


def test_one_fail_row_is_not_ok_and_is_named():
    outcome = evaluate_delete_rules([_rules("PASS", "FAIL"), _totals(1, 1)])
    assert not outcome.ok
    assert outcome.failing_rules == ["rule 2"]


def test_failed_total_alone_makes_the_run_fail():
    outcome = evaluate_delete_rules([_rules("PASS"), _totals(0, 1)])
    assert not outcome.ok


def test_no_rules_is_not_ok():
    outcome = evaluate_delete_rules([_rules(), _totals(0, 0)])
    assert not outcome.ok


def test_null_totals_count_as_zero():
    outcome = evaluate_delete_rules([_rules("PASS"), ResultSet(columns=("passed", "failed"), rows=[(None, None)])])
    assert outcome.ok


@pytest.mark.parametrize(
    "results",
    [
        [],
        [_rules("PASS")],
        [ResultSet(columns=("a", "b"), rows=[]), _totals(0, 0)],
        [_rules("PASS"), ResultSet(columns=("x",), rows=[(1,)])],
    ],
)
def test_unexpected_shapes_are_reported(results):
    with pytest.raises(UnexpectedOutputError):
        evaluate_delete_rules(results)
