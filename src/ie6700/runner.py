"""Run a course script statement by statement in one database session."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymysql

from .sqlscript import SqlSplitError, split_script


@dataclass(frozen=True)
class ResultSet:
    """Rows returned by one statement (or one result of a ``CALL``)."""

    columns: tuple[str, ...]
    rows: list[tuple[Any, ...]] = field(default_factory=list)
    source: str | None = None  # script path, when the rows came from a script
    line: int | None = None  # line where the statement starts
    heading: str | None = None  # numbered comment right before the statement, if any
    section: str | None = None  # top-level section the statement belongs to, if any

    @property
    def title(self) -> str:
        """The query's own heading, else its section, with the script location."""
        if self.heading:
            return self.heading
        where = f"{Path(self.source).name} line {self.line}" if self.source and self.line else None
        if self.section:
            return f"{self.section} - {where}" if where else self.section
        return where or "result"


class SqlScriptError(Exception):
    """A statement failed. Execution stopped at this statement."""

    def __init__(
        self,
        source: str,
        line: int,
        message: str,
        *,
        errno: int | None = None,
        preview: str | None = None,
    ) -> None:
        self.source = source
        self.line = line
        self.errno = errno
        self.message = message
        self.preview = preview
        code = f" (MySQL error {errno})" if errno is not None else ""
        lines = [f"{source}:{line}: {message}{code}"]
        if preview:
            lines.append(f"  statement: {preview}")
        super().__init__("\n".join(lines))


def run_script(conn: pymysql.connections.Connection, path: Path | str) -> list[ResultSet]:
    """Execute every statement of ``path`` in order on ``conn``.

    Returns one :class:`ResultSet` per result set, in script order. Stops at the
    first error and raises :class:`SqlScriptError`. The caller decides what to
    do with the connection; the course scripts run in one session so that
    ``SET @x``, temporary tables and ``START TRANSACTION`` work across statements.
    """
    source = str(path)
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        statements = split_script(text)
    except SqlSplitError as exc:
        raise SqlScriptError(source, exc.line, exc.message) from None

    results: list[ResultSet] = []
    with conn.cursor() as cur:
        for statement in statements:
            try:
                cur.execute(statement.sql)
                while True:
                    if cur.description is not None:
                        results.append(
                            ResultSet(
                                columns=tuple(column[0] for column in cur.description),
                                rows=[tuple(row) for row in cur.fetchall()],
                                source=source,
                                line=statement.line,
                                heading=statement.heading,
                                section=statement.section,
                            )
                        )
                    if not cur.nextset():
                        break
            except pymysql.MySQLError as exc:
                errno, message = _error_parts(exc)
                raise SqlScriptError(
                    source,
                    statement.line,
                    message,
                    errno=errno,
                    preview=_first_line(statement.sql),
                ) from exc
    return results


def _error_parts(exc: BaseException) -> tuple[int | None, str]:
    args = exc.args
    if len(args) >= 2 and isinstance(args[0], int):
        return args[0], str(args[1])
    return None, str(exc)


def _first_line(sql: str) -> str:
    first = sql.strip().splitlines()[0] if sql.strip() else ""
    return first if len(first) <= 120 else first[:117] + "..."
