# Proposal

## Involved Repositories

| Repository Name | Path | Edit Permission | Purpose |
| --- | --- | --- | --- |
| IE6700-py | repos/IE6700-py | [editable] | Current change context |

## Why

`IE6700-py` has the course MySQL assets (`mysql/marketplace.sql`, `mysql/seed/*.sql`, `mysql/queries.sql`, `mysql/delete_rules.sql`). Today the only ways to run them are Bash scripts (`db.sh`, `reset.sh`, `import_local.sh`) that need Docker, Bash and a `mysql` client. These do not work natively on Windows. The submission also requires a Python application that connects to MySQL and runs at least three embedded queries, and the repository has no Python project yet. Nothing checks automatically that the SQL still loads and produces the expected results.

## What Changes

- Add a Python project at the `IE6700-py` repository root, installable into a local `.venv`. It uses `pyproject.toml` with a pure-Python MySQL driver, so no compiler or system client library is needed on Windows, macOS or Linux.
- Document `.venv` creation, activation and installation for Windows (PowerShell and cmd), macOS and Linux in the root `README.md`.
- Add `.env`-based configuration. A `.env.example` provides a single connection string (`DATABASE_URL`), and `.env` is git-ignored. The CLI loads it automatically, and an environment variable overrides the file.
- Add a CLI (`python -m ie6700` and an `ie6700` console script) that runs the three course SQL files and prints the results as tables:
  - `load` runs `mysql/marketplace.sql`, then the three `mysql/seed/*.sql` files in order.
  - `queries` runs `mysql/queries.sql` and shows each result set.
  - `test` runs `mysql/delete_rules.sql` and shows the PASS/FAIL table.
  - `status` shows the server version and per-table row counts.
- Add a SQL script runner that handles what the `mysql` client does and a plain driver does not: `DELIMITER` directives, comments, `USE`, session variables (`SET @x`) and multiple result sets. This lets the existing SQL files run unmodified.
- Add GitHub Actions workflows that:
  - run the CLI against a MySQL 8.4 service container and assert the expected results, including 23 tables, the known seed row counts, 27 delete-rule PASS rows with 0 FAIL, and 0 violations in every data-health check in `queries.sql`;
  - install the project into a fresh `.venv` and run the unit tests on `ubuntu`, `windows` and `macos` runners.
- Add tests: unit tests for configuration and the script splitter, and integration tests for the expected SQL results.
- No existing SQL, seed data or Bash script is changed. The Bash scripts remain as an alternative path.

## Capabilities

### New Capabilities
- `python-environment-setup`: Python project layout and documented, cross-platform `.venv` install and run commands for Windows, macOS and Linux.
- `database-connection-config`: `.env`-based `DATABASE_URL` connection string loading, precedence rules, validation and secret-safe error messages.
- `sql-script-execution`: Running MySQL client-style `.sql` scripts (`DELIMITER`, comments, `USE`, session variables, multiple result sets) through a Python driver, with ordered execution and fail-fast error reporting.
- `course-sql-cli`: The `load`, `queries`, `test` and `status` commands and their tabular result display and exit codes.
- `sql-ci-validation`: GitHub Actions workflows and result assertions that prove the course SQL loads and gives the expected results, and that the Python setup works on Windows, macOS and Linux.

### Modified Capabilities
<!-- None. Existing specs under openspec/specs/ cover the AICR site and research records and are unrelated. -->

## Impact

- **Repository**: only `repos/IE6700-py` changes. The new Python project and workflows live at its root, next to the existing `mysql/` and `docs/` directories. Files under `mysql/` are read, not modified.
- **Dependencies (new)**: a pure-Python MySQL driver (PyMySQL), a `.env` loader (python-dotenv), a table renderer (e.g. `tabulate` or `rich`), and `pytest` for tests. All install through `pip` inside `.venv`.
- **External systems**: GitHub Actions. Full SQL validation uses a MySQL 8.4 service container, which is available only on Linux runners. Windows and macOS runners verify the `.venv` install, CLI startup and unit tests.
- **Runtime**: Python 3.10 or later and a reachable MySQL 8.x server, such as the existing Docker sandbox from `mysql/reset.sh` on `127.0.0.1:3307`. Docker is no longer required by the CLI itself.
- **Compatibility**: not breaking. The Bash scripts, the Docker setup and `mysql/.env.example` keep working. The new root `.env` is separate from `mysql/.env`.

### Code Change Table

| File Path | Change Type | Change Reason | Impact Scope |
| --- | --- | --- | --- |
| `repos/IE6700-py/pyproject.toml` | Add | Declare the package, dependencies, Python version and the `ie6700` console script | Python packaging, `.venv` install |
| `repos/IE6700-py/src/ie6700/__init__.py` | Add | Package marker and version | Package |
| `repos/IE6700-py/src/ie6700/__main__.py` | Add | Enable `python -m ie6700` | CLI entry |
| `repos/IE6700-py/src/ie6700/cli.py` | Add | Argument parsing and the `load`, `queries`, `test`, `status` commands with exit codes | CLI |
| `repos/IE6700-py/src/ie6700/config.py` | Add | Load `.env`, resolve and validate `DATABASE_URL`, mask the password in messages | Connection configuration |
| `repos/IE6700-py/src/ie6700/db.py` | Add | Open the MySQL connection (utf8mb4, multi-statement-safe) from the parsed settings | Database access |
| `repos/IE6700-py/src/ie6700/sqlscript.py` | Add | Split `.sql` scripts into statements, with `DELIMITER` support | SQL execution |
| `repos/IE6700-py/src/ie6700/runner.py` | Add | Execute scripts in order, collect result sets and report the failing file, line and statement | SQL execution |
| `repos/IE6700-py/src/ie6700/render.py` | Add | Render result sets as text tables | Result display |
| `repos/IE6700-py/src/ie6700/paths.py` | Add | Locate `mysql/*.sql` relative to the repository, independent of the working directory and OS | Cross-platform paths |
| `repos/IE6700-py/.env.example` | Add | Documented `DATABASE_URL` template | Configuration |
| `repos/IE6700-py/.gitignore` | Add | Ignore `.venv/`, `.env`, caches and build output | Repository hygiene |
| `repos/IE6700-py/README.md` | Modify | Keep the submission requirements, add setup, `.env` and CLI usage for each OS | Documentation |
| `repos/IE6700-py/tests/test_config.py` | Add | Unit tests for connection string parsing and precedence | Tests |
| `repos/IE6700-py/tests/test_sqlscript.py` | Add | Unit tests for splitting, including `DELIMITER` and comments | Tests |
| `repos/IE6700-py/tests/test_cli.py` | Add | CLI argument and exit code tests | Tests |
| `repos/IE6700-py/tests/integration/test_course_sql.py` | Add | Assert table counts, row counts, 27 PASS rows and zero health-check violations against a live MySQL | Tests, CI |
| `repos/IE6700-py/tests/expected/*.json` | Add | Expected row counts and result snapshots used by assertions | Tests, CI |
| `repos/IE6700-py/.github/workflows/ci.yml` | Add | Cross-platform `.venv` install and unit tests on ubuntu, windows and macos | CI |
| `repos/IE6700-py/.github/workflows/sql-validation.yml` | Add | MySQL 8.4 service container, load, queries, delete-rule tests and result assertions | CI |
