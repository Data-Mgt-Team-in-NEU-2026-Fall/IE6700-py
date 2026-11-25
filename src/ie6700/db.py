"""MySQL connection and catalogue helpers."""

from __future__ import annotations

import re

import pymysql

from .config import Settings

_VERSION_RE = re.compile(r"(\d+)\.(\d+)")


class UnsupportedServerError(Exception):
    """The server is MariaDB or a MySQL version other than 8.x."""


def check_server_version(version: str) -> None:
    """Raise :class:`UnsupportedServerError` unless ``version`` is MySQL 8.x."""
    text = version.strip()
    if "mariadb" in text.lower():
        raise UnsupportedServerError(
            f"The server reports MariaDB ({text}). This course schema needs MySQL 8.x."
        )
    match = _VERSION_RE.match(text)
    if match is None:
        raise UnsupportedServerError(
            f"Cannot read the server version ({text!r}). This course schema needs MySQL 8.x."
        )
    if int(match.group(1)) != 8:
        raise UnsupportedServerError(
            f"The server is MySQL {text}. This course schema needs MySQL 8.x."
        )


def connect(settings: Settings, *, database: str | None = None) -> pymysql.connections.Connection:
    """Open a connection with utf8mb4 and autocommit on.

    No default database is selected unless ``database`` is given. The course
    scripts select their own database with ``USE``.
    """
    return pymysql.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=database,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=10,
    )


def quote_identifier(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def server_version(conn: pymysql.connections.Connection) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        (version,) = cur.fetchone()
    return str(version)


def server_info(conn: pymysql.connections.Connection) -> tuple[str, str, str]:
    """Return ``(version, character_set_server, collation_server)``."""
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION(), @@character_set_server, @@collation_server")
        version, charset, collation = cur.fetchone()
    return str(version), str(charset), str(collation)


def schema_exists(conn: pymysql.connections.Connection, schema: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (schema,),
        )
        (count,) = cur.fetchone()
    return int(count) == 1


def base_table_names(conn: pymysql.connections.Connection, schema: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
            (schema,),
        )
        return [str(row[0]) for row in cur.fetchall()]


def table_counts(conn: pymysql.connections.Connection, schema: str) -> list[tuple[str, int]]:
    """Exact ``COUNT(*)`` for every base table of ``schema``, in name order.

    ``information_schema`` row estimates are approximate for InnoDB, so they are not used.
    """
    counts: list[tuple[str, int]] = []
    with conn.cursor() as cur:
        for table in base_table_names(conn, schema):
            cur.execute(
                f"SELECT COUNT(*) FROM {quote_identifier(schema)}.{quote_identifier(table)}"
            )
            (count,) = cur.fetchone()
            counts.append((table, int(count)))
    return counts
