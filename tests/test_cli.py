import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ie6700.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def _isolated(tmp_path: Path) -> dict:
    """Arguments that stop main() from reading any .env or the real environment."""
    return {"environ": {}, "cwd": tmp_path, "repo_root": tmp_path / "root"}


def test_help_lists_the_four_commands(capsys):
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    for command in ("load", "queries", "test", "status"):
        assert command in out


def test_each_subcommand_has_help(capsys):
    for command in ("load", "queries", "test", "status"):
        assert main([command, "--help"]) == 0
    assert "--format" in capsys.readouterr().out


def test_unknown_command_prints_usage_and_exits_2(capsys):
    assert main(["frobnicate"], environ={}) == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_no_command_exits_2(capsys):
    assert main([], environ={}) == 2


def test_missing_configuration_exits_2_before_any_connection(tmp_path, capsys):
    assert main(["load"], **_isolated(tmp_path)) == 2
    err = capsys.readouterr().err
    assert ".env.example" in err
    assert "not set" in err


def test_failing_connection_never_prints_the_password(capsys):
    environ = {"DATABASE_URL": "mysql://root:secret@127.0.0.1:1/seattle_marketplace"}
    for command in (["load"], ["queries"], ["status"], ["test"]):
        capsys.readouterr()
        assert main(command, environ=environ) == 1
        captured = capsys.readouterr()
        assert "***" in captured.err
        assert "127.0.0.1" in captured.err
        assert "secret" not in captured.out + captured.err


def test_module_entry_point_starts_the_cli():
    result = subprocess.run(
        [sys.executable, "-m", "ie6700", "--help"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "queries" in result.stdout


def test_queries_json_writes_only_one_json_document(loaded_db, capsys):
    # Uses the course database; skipped when no DATABASE_URL is configured.
    assert main(["queries", "--format", "json"]) == 0
    captured = capsys.readouterr()
    document = json.loads(captured.out)
    assert isinstance(document, list)
    assert len(document) > 0
    assert "queries.sql" in captured.err or "result set" in captured.err
    assert "result set" not in captured.out


class _FakeConnection:
    def close(self) -> None:
        pass


def test_test_command_prints_the_full_table_and_exits_1_on_a_fail_row(monkeypatch, capsys):
    from ie6700 import cli
    from ie6700.runner import ResultSet

    rules = ResultSet(
        columns=("seq", "rule_name", "expected", "actual", "leftover", "result"),
        rows=[
            (1, "first rule", "blocked", "blocked", None, "PASS"),
            (2, "second rule", "blocked", "allowed", None, "FAIL"),
        ],
        source="delete_rules.sql",
        line=10,
    )
    totals = ResultSet(columns=("passed", "failed"), rows=[(1, 1)], source="delete_rules.sql", line=11)
    monkeypatch.setattr(cli.db, "connect", lambda settings, **kwargs: _FakeConnection())
    monkeypatch.setattr(cli.db, "schema_exists", lambda conn, schema: True)
    monkeypatch.setattr(cli, "run_script", lambda conn, path: [rules, totals])

    status = main(["test"], environ={"DATABASE_URL": "mysql://root:secret@127.0.0.1:3307/x"})

    captured = capsys.readouterr()
    assert status == 1
    assert "first rule" in captured.out and "second rule" in captured.out  # table printed in full
    assert "1 passed, 1 failed" in captured.out
    assert "FAIL: second rule" in captured.err
    assert "secret" not in captured.out + captured.err


def test_missing_course_database_gives_a_load_hint_and_exit_1(monkeypatch, capsys):
    from ie6700 import cli

    monkeypatch.setattr(cli.db, "connect", lambda settings, **kwargs: _FakeConnection())
    monkeypatch.setattr(cli.db, "schema_exists", lambda conn, schema: False)

    for command in (["queries"], ["test"]):
        capsys.readouterr()
        assert main(command, environ={"DATABASE_URL": "mysql://root:pw@127.0.0.1:3307/x"}) == 1
        assert "ie6700 load" in capsys.readouterr().err
