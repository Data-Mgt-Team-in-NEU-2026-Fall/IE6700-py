import pytest

from ie6700.db import UnsupportedServerError, check_server_version


@pytest.mark.parametrize(
    "version",
    ["8.0.36", "8.4.3", "8.0.36-0ubuntu0.22.04.1", "8.4.0-commercial", " 8.4.3 "],
)
def test_mysql_8_is_accepted(version: str):
    check_server_version(version)


@pytest.mark.parametrize(
    "version",
    [
        "10.11.6-MariaDB",
        "5.5.5-10.6.12-MariaDB-0ubuntu0.22.04.1",
        "5.7.44",
        "9.0.1",
        "not a version",
        "",
    ],
)
def test_mariadb_and_other_versions_are_rejected(version: str):
    with pytest.raises(UnsupportedServerError) as info:
        check_server_version(version)
    assert "8.x" in str(info.value) or "MariaDB" in str(info.value)
