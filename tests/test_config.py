from pathlib import Path

import pytest

from ie6700.config import ConfigError, find_env_file, load_settings, parse_database_url

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / ".env.example"


def _no_file_settings(environ, tmp_path):
    """Load settings with no .env anywhere the search looks."""
    return load_settings(environ=environ, cwd=tmp_path, repo_root=tmp_path / "root")


def test_value_is_read_from_env_file(tmp_path: Path):
    (tmp_path / ".env").write_text(
        "DATABASE_URL=mysql://root:secret@127.0.0.1:3307/seattle_marketplace\n", encoding="utf-8"
    )
    settings = load_settings(environ={}, cwd=tmp_path, repo_root=tmp_path / "root")
    assert settings.host == "127.0.0.1"
    assert settings.port == 3307
    assert settings.user == "root"
    assert settings.password == "secret"
    assert settings.database == "seattle_marketplace"
    assert settings.source == str(tmp_path / ".env")


def test_env_file_in_repository_root_is_used_when_working_directory_has_none(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".env").write_text("DATABASE_URL=mysql://u:p@db.local:3399/x\n", encoding="utf-8")
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    settings = load_settings(environ={}, cwd=cwd, repo_root=root)
    assert settings.host == "db.local"
    assert settings.port == 3399


def test_working_directory_env_file_wins_over_repository_root(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".env").write_text("DATABASE_URL=mysql://u:p@root-host/x\n", encoding="utf-8")
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / ".env").write_text("DATABASE_URL=mysql://u:p@cwd-host/x\n", encoding="utf-8")
    assert find_env_file(cwd, root) == cwd / ".env"
    assert load_settings(environ={}, cwd=cwd, repo_root=root).host == "cwd-host"


def test_environment_overrides_env_file(tmp_path: Path):
    (tmp_path / ".env").write_text("DATABASE_URL=mysql://root:a@file-host:3307/db\n", encoding="utf-8")
    settings = load_settings(
        environ={"DATABASE_URL": "mysql://root:b@env-host:3308/db"},
        cwd=tmp_path,
        repo_root=tmp_path / "root",
    )
    assert settings.host == "env-host"
    assert settings.port == 3308
    assert settings.password == "b"
    assert settings.source == "DATABASE_URL"


def test_default_port_is_3306():
    assert parse_database_url("mysql://root:pw@localhost/seattle_marketplace").port == 3306


def test_percent_encoded_password_is_decoded():
    settings = parse_database_url("mysql://app:p%40ss%2Fword@localhost:3306/seattle_marketplace")
    assert settings.password == "p@ss/word"


def test_database_may_be_omitted():
    settings = parse_database_url("mysql://root:pw@127.0.0.1:3307")
    assert settings.database is None
    assert settings.safe_url == "mysql://root:***@127.0.0.1:3307"


def test_missing_value_says_how_to_fix_it(tmp_path: Path):
    with pytest.raises(ConfigError) as info:
        _no_file_settings({}, tmp_path)
    assert ".env.example" in str(info.value)
    assert "not set" in str(info.value)


def test_env_file_without_the_variable_is_reported(tmp_path: Path):
    (tmp_path / ".env").write_text("OTHER=1\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="not set in"):
        load_settings(environ={}, cwd=tmp_path, repo_root=tmp_path / "root")


@pytest.mark.parametrize(
    "raw",
    [
        "mysql://root:pw@:3307/seattle_marketplace",  # no host
        "mysql://@127.0.0.1:3307/seattle_marketplace",  # no user name
        "mysql://root:pw@127.0.0.1:notaport/seattle_marketplace",  # port is not a number
        "mysql://root:pw@127.0.0.1:99999/seattle_marketplace",  # port out of range
        "mysql://root:pw@127.0.0.1/seattle/marketplace",  # extra path segment
    ],
)
def test_malformed_value_is_rejected(raw: str):
    with pytest.raises(ConfigError, match="malformed") as info:
        parse_database_url(raw)
    assert "pw" not in str(info.value)


@pytest.mark.parametrize(
    "raw",
    [
        "postgres://root:secret@127.0.0.1:5432/app",
        "root:secret@127.0.0.1:3307/seattle_marketplace",
    ],
)
def test_wrong_scheme_is_rejected_without_echoing_the_password(raw: str):
    with pytest.raises(ConfigError) as info:
        parse_database_url(raw)
    message = str(info.value)
    assert "Only mysql:// is supported" in message
    assert "secret" not in message


def test_safe_url_hides_password_and_repr_does_too():
    settings = parse_database_url("mysql://root:secret@127.0.0.1:3307/seattle_marketplace")
    assert settings.safe_url == "mysql://root:***@127.0.0.1:3307/seattle_marketplace"
    assert "secret" not in settings.safe_url
    assert "secret" not in repr(settings)


def test_ipv6_host_is_bracketed_in_safe_url():
    settings = parse_database_url("mysql://root:pw@[::1]:3307/db")
    assert settings.host == "::1"
    assert settings.safe_url == "mysql://root:***@[::1]:3307/db"


def test_env_example_parses_to_the_local_sandbox():
    raw = EXAMPLE.read_text(encoding="utf-8")
    values = {}
    for line in raw.splitlines():
        if line.startswith("DATABASE_URL="):
            values["DATABASE_URL"] = line.split("=", 1)[1]
    settings = parse_database_url(values["DATABASE_URL"])
    assert settings.host == "127.0.0.1"
    assert settings.port == 3307
    assert settings.database == "seattle_marketplace"
