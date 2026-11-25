"""Locate the course SQL files.

The files live in ``<repository>/mysql``. The package finds them relative to its
own location, so an editable install (``pip install -e .``) works from any
working directory. ``IE6700_SQL_DIR`` overrides the location.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

SQL_DIR_ENV = "IE6700_SQL_DIR"

REPO_ROOT = Path(__file__).resolve().parents[2]

# Order used by `load`: the schema first, then the three seed files.
LOAD_SEQUENCE: tuple[str, ...] = (
    "marketplace.sql",
    "seed/01_identity.sql",
    "seed/02_marketplace.sql",
    "seed/03_messaging_reviews_reports.sql",
)
QUERIES_FILE = "queries.sql"
DELETE_RULES_FILE = "delete_rules.sql"


class SqlFilesError(Exception):
    """The SQL directory or one of the course files is missing."""


def sql_dir(environ: Mapping[str, str] | None = None) -> Path:
    """Return the directory that holds the course SQL files."""
    env = os.environ if environ is None else environ
    override = (env.get(SQL_DIR_ENV) or "").strip()
    base = Path(override).expanduser() if override else REPO_ROOT / "mysql"
    if not base.is_dir():
        raise SqlFilesError(
            f"SQL directory not found: {base}. Run ie6700 from a checkout that has the "
            f"mysql/ folder, install with 'pip install -e .' from the repository, or set "
            f"{SQL_DIR_ENV} to the folder that holds marketplace.sql."
        )
    return base


def script_path(name: str, environ: Mapping[str, str] | None = None) -> Path:
    """Return the path of one course SQL file, checking that it exists."""
    path = sql_dir(environ) / name
    if not path.is_file():
        raise SqlFilesError(
            f"Missing SQL file: {path}. Set {SQL_DIR_ENV} to a folder that holds the "
            f"complete mysql/ file set."
        )
    return path


def load_files(environ: Mapping[str, str] | None = None) -> list[tuple[str, Path]]:
    """Return ``(name, path)`` for each file of the load sequence, in order."""
    return [(name, script_path(name, environ)) for name in LOAD_SEQUENCE]


def queries_path(environ: Mapping[str, str] | None = None) -> Path:
    return script_path(QUERIES_FILE, environ)


def delete_rules_path(environ: Mapping[str, str] | None = None) -> Path:
    return script_path(DELETE_RULES_FILE, environ)
