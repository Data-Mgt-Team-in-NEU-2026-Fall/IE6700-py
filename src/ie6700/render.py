"""Turn result sets into text tables, CSV or JSON.

Output has no terminal-width detection or colour, so it is identical on every
operating system and easy to compare in tests.
"""

from __future__ import annotations

import csv
import datetime
import io
import json
import sys
from typing import Any, Sequence, TextIO

from tabulate import tabulate

from .runner import ResultSet

FORMATS = ("table", "csv", "json")


def cell_text(value: Any) -> str:
    """Text for one cell. ``NULL`` is shown as the word NULL."""
    if value is None:
        return "NULL"
    if isinstance(value, datetime.datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)  # int, Decimal, timedelta and str


def json_value(value: Any) -> Any:
    """A JSON-safe value. Decimals and dates become strings so no precision is lost."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime.datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def table_text(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    text_rows = [[cell_text(value) for value in row] for row in rows]
    return tabulate(text_rows, headers=list(columns), tablefmt="simple", disable_numparse=True)


def csv_text(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([cell_text(value) for value in row])
    return buffer.getvalue()


def results_json(results: Sequence[ResultSet]) -> str:
    document = [
        {
            "source": result.source,
            "line": result.line,
            "heading": result.heading,
            "section": result.section,
            "columns": list(result.columns),
            "row_count": len(result.rows),
            "rows": [[json_value(value) for value in row] for row in result.rows],
        }
        for result in results
    ]
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def render_results(results: Sequence[ResultSet], fmt: str, out: TextIO) -> None:
    """Write result sets to ``out`` in the requested format."""
    if fmt == "json":
        write_text(out, results_json(results))
        return
    for index, result in enumerate(results):
        if index:
            write_text(out, "\n")
        if fmt == "table":
            count = len(result.rows)
            noun = "row" if count == 1 else "rows"
            write_text(out, f"== {result.title} ({count} {noun})\n")
            write_text(out, table_text(result.columns, result.rows) + "\n")
        elif fmt == "csv":
            write_text(out, csv_text(result.columns, result.rows))
        else:
            raise ValueError(f"unknown format: {fmt}")


def write_text(stream: TextIO, text: str) -> None:
    """Write text, replacing characters the stream's encoding cannot hold.

    This keeps output working on legacy consoles whose encoding is not UTF-8.
    """
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        stream.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def configure_stdio() -> None:
    """Use UTF-8 with replacement on the standard streams where that is supported."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
