"""Read the database connection string from the environment or a .env file.

``DATABASE_URL`` takes the form ``mysql://user:password@host:port/database``.
The environment wins over the file. The file is ``.env`` in the working
directory, or in the repository root when the working directory has none.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from dotenv import dotenv_values

from .paths import REPO_ROOT

ENV_VAR = "DATABASE_URL"
ENV_FILE_NAME = ".env"
EXAMPLE_FILE_NAME = ".env.example"
DEFAULT_PORT = 3306


class ConfigError(Exception):
    """DATABASE_URL is missing or cannot be used. The message never contains the password."""


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    user: str
    password: str = field(repr=False)
    database: str | None
    source: str

    @property
    def safe_url(self) -> str:
        """The connection target with the password replaced by ``***``."""
        host = f"[{self.host}]" if ":" in self.host else self.host
        auth = f"{self.user}:***@" if self.password else f"{self.user}@"
        database = f"/{self.database}" if self.database else ""
        return f"mysql://{auth}{host}:{self.port}{database}"


def find_env_file(cwd: Path, repo_root: Path) -> Path | None:
    """Return the ``.env`` to read: the working directory first, then the repository root."""
    for folder in (cwd, repo_root):
        candidate = folder / ENV_FILE_NAME
        if candidate.is_file():
            return candidate
    return None


def parse_database_url(raw: str, source: str = ENV_VAR) -> Settings:
    """Parse a ``mysql://`` URL. Raises :class:`ConfigError` without echoing the URL."""
    try:
        parts = urlsplit(raw.strip())
        port = parts.port
    except ValueError:
        raise ConfigError(_malformed("it cannot be parsed")) from None

    if parts.scheme.lower() != "mysql":
        raise ConfigError(
            f"{ENV_VAR} must start with mysql://. Only mysql:// is supported. "
            f"See {EXAMPLE_FILE_NAME} for the format."
        )
    try:
        host = parts.hostname
    except ValueError:
        raise ConfigError(_malformed("the host cannot be parsed")) from None
    if not host:
        raise ConfigError(_malformed("no host is given"))

    user = unquote(parts.username or "")
    if not user:
        raise ConfigError(_malformed("no user name is given"))

    password = unquote(parts.password) if parts.password is not None else ""
    database_name = unquote(parts.path[1:]) if parts.path.startswith("/") else unquote(parts.path)
    if "/" in database_name:
        raise ConfigError(_malformed("the database name cannot contain '/'"))

    return Settings(
        host=host,
        port=port if port is not None else DEFAULT_PORT,
        user=user,
        password=password,
        database=database_name or None,
        source=source,
    )


def load_settings(
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    repo_root: Path | None = None,
) -> Settings:
    """Return the settings from the environment, or else from the first ``.env`` found."""
    env = os.environ if environ is None else environ
    raw = (env.get(ENV_VAR) or "").strip()
    source = ENV_VAR
    if not raw:
        env_file = find_env_file(
            Path.cwd() if cwd is None else Path(cwd),
            REPO_ROOT if repo_root is None else Path(repo_root),
        )
        if env_file is None:
            raise ConfigError(
                f"{ENV_VAR} is not set. Copy {EXAMPLE_FILE_NAME} to {ENV_FILE_NAME} "
                f"and set it, or set the {ENV_VAR} environment variable."
            )
        raw = (dotenv_values(env_file).get(ENV_VAR) or "").strip()
        source = str(env_file)
        if not raw:
            raise ConfigError(
                f"{ENV_VAR} is not set in {env_file}. Copy {EXAMPLE_FILE_NAME} to "
                f"{ENV_FILE_NAME} and set it, or set the {ENV_VAR} environment variable."
            )
    return parse_database_url(raw, source)


def _malformed(reason: str) -> str:
    return (
        f"{ENV_VAR} is malformed: {reason}. Expected mysql://user:password@host:port/database "
        f"(see {EXAMPLE_FILE_NAME})."
    )
