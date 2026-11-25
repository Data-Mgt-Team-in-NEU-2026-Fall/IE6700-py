"""Command-line interface: ``ie6700 load | queries | test | status``.

Exit status: 0 success, 1 a database, SQL or verification failure, 2 a usage or
configuration problem. Progress goes to standard error, so ``--format csv`` and
``--format json`` write only data to standard output.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

import pymysql

from . import __version__, db
from .config import ConfigError, Settings, load_settings
from .course import (
    ALREADY_EXISTS_ERRNOS,
    COURSE_SCHEMA,
    EXPECTED_TABLE_COUNT,
    RESET_HINT,
    UnexpectedOutputError,
    evaluate_delete_rules,
    load_course,
)
from .paths import SqlFilesError, delete_rules_path, queries_path
from .render import FORMATS, configure_stdio, render_results, write_text
from .runner import ResultSet, SqlScriptError, run_script


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ie6700",
        description="Load, query and check the IE6700 course MySQL database.",
    )
    parser.add_argument("--version", action="version", version=f"ie6700 {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    commands.add_parser(
        "load",
        help="create the course database from marketplace.sql and the seed files",
    )
    queries = commands.add_parser("queries", help="run queries.sql and print every result set")
    _add_format(queries)
    tests = commands.add_parser("test", help="run delete_rules.sql and print the PASS/FAIL table")
    _add_format(tests)
    status = commands.add_parser("status", help="show the server version and row count per table")
    _add_format(status)
    return parser


def _add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="table",
        help="output format (default: table)",
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: dict[str, str] | None = None,
    cwd: Path | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run the CLI and return the exit status."""
    configure_stdio()
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # --help and usage errors; argparse has printed the text
        return int(exc.code or 0)

    out, err = sys.stdout, sys.stderr
    try:
        settings = load_settings(environ=environ, cwd=cwd, repo_root=repo_root)
    except ConfigError as exc:
        write_text(err, f"ie6700: configuration error: {exc}\n")
        return 2

    try:
        return _dispatch(args.command, args, settings, out, err)
    except SqlScriptError as exc:
        _error(err, settings, str(exc))
    except db.UnsupportedServerError as exc:
        _error(err, settings, str(exc))
    except SqlFilesError as exc:
        _error(err, settings, str(exc))
    except pymysql.MySQLError as exc:
        _error(err, settings, f"MySQL error at {settings.safe_url}: {_driver_message(exc)}")
    return 1


def _dispatch(command: str, args: argparse.Namespace, settings: Settings, out: TextIO, err: TextIO) -> int:
    if command == "load":
        return cmd_load(settings, out, err)
    if command == "queries":
        return cmd_queries(settings, args.format, out, err)
    if command == "test":
        return cmd_test(settings, args.format, out, err)
    if command == "status":
        return cmd_status(settings, args.format, out, err)
    raise AssertionError(f"unhandled command: {command}")


def cmd_load(settings: Settings, out: TextIO, err: TextIO) -> int:
    conn = db.connect(settings)
    try:
        version = db.server_version(conn)
        db.check_server_version(version)
        _log(err, f"Connected to {settings.safe_url} (MySQL {version}).")

        def start(name: str) -> None:
            write_text(out, f"{name} ... ")

        def done(name: str) -> None:
            write_text(out, "ok\n")

        try:
            load_course(conn, on_file_start=start, on_file_done=done)
        except SqlScriptError as exc:
            write_text(out, "failed\n")
            if exc.errno in ALREADY_EXISTS_ERRNOS:
                _error(err, settings, f"{exc}\n{RESET_HINT}")
            else:
                _error(err, settings, str(exc))
            return 1

        tables = len(db.base_table_names(conn, COURSE_SCHEMA))
        if tables != EXPECTED_TABLE_COUNT:
            _error(
                err,
                settings,
                f"{COURSE_SCHEMA} has {tables} base tables; expected {EXPECTED_TABLE_COUNT}.",
            )
            return 1
        write_text(out, f"Verified {tables} base tables in {COURSE_SCHEMA}.\n")
        return 0
    finally:
        conn.close()


def cmd_queries(settings: Settings, fmt: str, out: TextIO, err: TextIO) -> int:
    results = _run_on_course_database(settings, err, lambda conn: run_script(conn, queries_path()))
    if results is None:
        return 1
    render_results(results, fmt, out)
    _log(err, f"queries.sql: {len(results)} result set(s).")
    return 0


def cmd_test(settings: Settings, fmt: str, out: TextIO, err: TextIO) -> int:
    results = _run_on_course_database(settings, err, lambda conn: run_script(conn, delete_rules_path()))
    if results is None:
        return 1
    try:
        outcome = evaluate_delete_rules(results)
    except UnexpectedOutputError as exc:
        _error(err, settings, str(exc))
        return 1

    render_results(results, fmt, out)
    summary = (
        f"Delete rules: {outcome.passed} passed, {outcome.failed} failed "
        f"of {outcome.rule_count} rules."
    )
    _log(out if fmt == "table" else err, summary)
    if outcome.ok:
        return 0
    for name in outcome.failing_rules:
        _log(err, f"FAIL: {name}")
    if outcome.rule_count == 0:
        _error(err, settings, "delete_rules.sql returned no rules.")
    return 1


def cmd_status(settings: Settings, fmt: str, out: TextIO, err: TextIO) -> int:
    conn = db.connect(settings)
    try:
        version, charset, collation = db.server_info(conn)
        server = ResultSet(
            columns=("mysql_version", "character_set_server", "collation_server"),
            rows=[(version, charset, collation)],
            heading="Server",
        )
        if not db.schema_exists(conn, COURSE_SCHEMA):
            render_results([server], fmt, out)
            _error(err, settings, f"The database {COURSE_SCHEMA} does not exist. Run ie6700 load first.")
            return 1
        tables = ResultSet(
            columns=("table", "rows"),
            rows=[(name, count) for name, count in db.table_counts(conn, COURSE_SCHEMA)],
            heading=f"Tables in {COURSE_SCHEMA}",
        )
    finally:
        conn.close()
    render_results([server, tables], fmt, out)
    _log(err, f"{len(tables.rows)} table(s) in {COURSE_SCHEMA}.")
    return 0


def _run_on_course_database(settings: Settings, err: TextIO, action) -> list[ResultSet] | None:
    """Run ``action(conn)`` on a connection after checking that the course database exists."""
    conn = db.connect(settings)
    try:
        if not db.schema_exists(conn, COURSE_SCHEMA):
            _error(err, settings, f"The database {COURSE_SCHEMA} does not exist. Run ie6700 load first.")
            return None
        return action(conn)
    finally:
        conn.close()


def _log(stream: TextIO, message: str) -> None:
    _flush_stdout(stream)
    write_text(stream, message + "\n")


def _error(stream: TextIO, settings: Settings, message: str) -> None:
    """Write an error, with the password replaced by ``***`` everywhere it appears."""
    text = message
    if settings.password:
        text = text.replace(settings.password, "***")
    _flush_stdout(stream)
    write_text(stream, f"ie6700: error: {text}\n")


def _flush_stdout(stream: TextIO) -> None:
    """Keep progress on stdout in order with messages on stderr when both share a log."""
    if stream is not sys.stdout:
        sys.stdout.flush()


def _driver_message(exc: pymysql.MySQLError) -> str:
    args = exc.args
    if len(args) >= 2:
        return f"({args[0]}) {args[1]}"
    return str(exc)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
