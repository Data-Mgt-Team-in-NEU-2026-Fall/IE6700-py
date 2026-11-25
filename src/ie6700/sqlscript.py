"""Split a MySQL client-style ``.sql`` script into statements.

The course files are written for the ``mysql`` command-line client. It understands
``DELIMITER`` and skips quoted text and comments when it looks for the end of a
statement. A database driver sends whatever it is given as one statement, so the
script is split here first. This module only splits text; it never runs SQL.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

__all__ = ["SqlSplitError", "Statement", "split_script"]

# "DELIMITER //" at the start of a statement, alone on its line.
_DELIMITER_RE = re.compile(r"DELIMITER[ \t]+(\S+)[ \t]*(?=\n|\Z)", re.IGNORECASE)
# A numbered heading comment such as "1.2 UC-1102 My listings" or "1. Identity".
_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+\S")
# A top-level section heading such as "6. Changes (...)": one number, then a dot.
_SECTION_RE = re.compile(r"^\d+\.\s+\S")
# MySQL starts a "--" comment only when whitespace or a control character follows.
_AFTER_DASHES = " \t\n\x0b\x0c"


@dataclass(frozen=True)
class Statement:
    """One statement from a script."""

    line: int  # 1-based line on which the statement's first token starts
    sql: str  # statement text without its delimiter and without leading comments
    heading: str | None  # numbered comment right before the statement, e.g. "1.2 UC-1102 ..."
    section: str | None  # nearest top-level section comment before it, e.g. "6. Changes ..."


class SqlSplitError(Exception):
    """The script ends inside a quoted string or a block comment."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


def split_script(text: str) -> list[Statement]:
    """Split script text into statements, in order.

    Comment-only chunks and empty statements produce nothing. Conditional
    comments (``/*! ... */`` and ``/*+ ... */``) stay inside the statement text.
    """
    text = text.lstrip("﻿").replace("\r\n", "\n")
    n = len(text)
    line_starts = [0]
    line_starts.extend(index + 1 for index, ch in enumerate(text) if ch == "\n")

    def line_of(index: int) -> int:
        return bisect.bisect_right(line_starts, index)

    statements: list[Statement] = []
    comments: list[str] = []  # comment texts seen since the last statement ended
    section: str | None = None  # last top-level section comment seen so far
    delimiter = ";"
    start: int | None = None  # index of the current statement's first character
    start_line = 0
    i = 0
    while i < n:
        if text.startswith(delimiter, i):
            if start is not None:
                statements.append(
                    Statement(start_line, text[start:i].strip(), _heading(comments), section)
                )
                start = None
            comments = []
            i += len(delimiter)
            continue

        ch = text[i]
        if start is None:
            if ch.isspace():
                i += 1
                continue
            if _starts_dash_comment(text, i):
                end = _line_end(text, i)
                comments.append(text[i + 2 : end].strip())
                section = _section_or(comments[-1], section)
                i = end
                continue
            if ch == "#":
                end = _line_end(text, i)
                comments.append(text[i + 1 : end].strip())
                section = _section_or(comments[-1], section)
                i = end
                continue
            if text.startswith("/*", i) and not text.startswith(("/*!", "/*+"), i):
                i = _must_end(_block_comment_end(text, i), line_of(i), "block comment")
                continue
            directive = _DELIMITER_RE.match(text, i)
            if directive:
                delimiter = directive.group(1)
                comments = []
                i = directive.end()
                continue
            start = i
            start_line = line_of(i)

        # Inside a statement: skip what may hide the delimiter, then move on.
        if ch in "'\"`":
            i = _must_end(_quoted_end(text, i), line_of(i), "quoted text")
        elif _starts_dash_comment(text, i) or ch == "#":
            i = _line_end(text, i)
        elif text.startswith("/*", i):
            i = _must_end(_block_comment_end(text, i), line_of(i), "block comment")
        else:
            i += 1

    if start is not None:
        statements.append(
            Statement(start_line, text[start:].strip(), _heading(comments), section)
        )
    return statements


def _starts_dash_comment(text: str, index: int) -> bool:
    if not text.startswith("--", index):
        return False
    return index + 2 >= len(text) or text[index + 2] in _AFTER_DASHES


def _line_end(text: str, index: int) -> int:
    end = text.find("\n", index)
    return len(text) if end == -1 else end


def _quoted_end(text: str, start: int) -> int:
    """Index just past the quoted text that starts at ``start``, or -1 if unterminated."""
    quote = text[start]
    n = len(text)
    j = start + 1
    while j < n:
        ch = text[j]
        if ch == "\\" and quote != "`":
            j += 2
        elif ch == quote:
            if j + 1 < n and text[j + 1] == quote:
                j += 2  # doubled quote inside the text
            else:
                return j + 1
        else:
            j += 1
    return -1


def _block_comment_end(text: str, start: int) -> int:
    end = text.find("*/", start + 2)
    return -1 if end == -1 else end + 2


def _must_end(index: int, line: int, what: str) -> int:
    if index < 0:
        raise SqlSplitError(line, f"unterminated {what}")
    return index


def _heading(comments: list[str]) -> str | None:
    for comment in reversed(comments):
        if _HEADING_RE.match(comment):
            return comment
    return None


def _section_or(comment: str, current: str | None) -> str | None:
    return comment if _SECTION_RE.match(comment) else current
