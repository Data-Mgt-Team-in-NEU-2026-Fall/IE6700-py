"""Helpers shared by the analytics modules: connection handling, output and exit statuses."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import pymysql
from tabulate import tabulate

from .. import db
from ..config import ConfigError, load_settings
from ..course import COURSE_SCHEMA

EXIT_OK = 0
EXIT_FAILURE = 1  # a database or SQL failure
EXIT_USAGE = 2  # a bad argument or configuration

Connection = pymysql.connections.Connection

_CENT = Decimal("0.01")
_TENTH = Decimal("0.1")


class InvalidInput(ValueError):
    """A user argument that the query cannot honour (for example min price above max price)."""


def money(value: Decimal | None) -> str:
    """Format a price with two decimals, or ``-`` when there is no value."""
    if value is None:
        return "-"
    return str(Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP))


def percent(part: int, whole: int) -> str:
    """Format ``part / whole`` as a percentage with one decimal, or ``-`` when ``whole`` is 0."""
    if whole == 0:
        return "-"
    share = (Decimal(part) * 100 / Decimal(whole)).quantize(_TENTH, rounding=ROUND_HALF_UP)
    return f"{share}%"


def average(total: Decimal | int, count: int, places: int = 2) -> str:
    """Format ``total / count`` with ``places`` decimals, or ``-`` when ``count`` is 0."""
    if count == 0:
        return "-"
    value = Decimal(total) / Decimal(count)
    return str(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def print_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    # disable_numparse keeps pre-formatted values such as "0.00" exactly as written.
    print(tabulate(rows, headers=list(headers), tablefmt="simple", disable_numparse=True))
    print()


def run_with_connection(action: Callable[[Connection], int]) -> int:
    """Open the course database, run ``action`` and turn failures into exit statuses.

    The password is never printed: errors use the redacted ``safe_url``.
    """
    try:
        settings = load_settings()
    except ConfigError as exc:
        return _fail(str(exc), EXIT_USAGE)
    try:
        conn = db.connect(settings, database=COURSE_SCHEMA)
    except pymysql.MySQLError as exc:
        return _fail(f"cannot open {COURSE_SCHEMA} on {settings.safe_url}: {exc}", EXIT_FAILURE)
    try:
        db.check_server_version(db.server_version(conn))
        return action(conn)
    except InvalidInput as exc:
        return _fail(str(exc), EXIT_USAGE)
    except (db.UnsupportedServerError, pymysql.MySQLError) as exc:
        return _fail(str(exc), EXIT_FAILURE)
    finally:
        conn.close()


def _fail(message: str, status: int) -> int:
    print(f"error: {message}", file=sys.stderr)
    return status
