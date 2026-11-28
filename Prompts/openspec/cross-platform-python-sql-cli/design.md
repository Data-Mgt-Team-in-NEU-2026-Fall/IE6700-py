# Design

## Context

Motivation and scope are in `proposal.md`. Requirements are in `specs/`. This document covers how to build it.

Current state of `repos/IE6700-py`:

- `mysql/` holds the course SQL: `marketplace.sql` (schema, creates and selects `seattle_marketplace`), `seed/01..03_*.sql` (data), `queries.sql` (about 750 lines; parameters are set with `SET @var`, section 6 writes inside `START TRANSACTION … ROLLBACK`, section 8 is the data-health check) and `delete_rules.sql` (uses `DELIMITER //` to define a stored procedure, a temporary table and a final PASS/FAIL result).
- The scripts target MySQL 8.x only (`utf8mb4_0900_ai_ci`, `CHECK` constraints, `ENUM`). The existing Docker sandbox listens on `127.0.0.1:3307` with root password `ie6700_local_root`.
- The repository has no Python code, no `.github/`, and a root `README.md` that holds only the submission requirements.
- Dev machine for authoring is Linux. The tool must also work on Windows and macOS with Python 3.10 or later.

The key technical gap: `DELIMITER` is a client directive, not SQL. A driver sends exactly what it is given, so the course files cannot be passed to it whole. The existing files must stay untouched (they are the deliverable and are also used by the Bash scripts).

## Goals / Non-Goals

**Goals:**

- Run the existing `.sql` files byte-for-byte, on all three operating systems, with only `pip` and a MySQL server.
- Make failures obvious: which file, which line, which server error.
- Make CI assert real results, with expectations stored in the repository and reviewable in diffs.

**Non-Goals:**

- Not a general MySQL client or a replacement for the `mysql` shell. It supports the syntax the course files use, plus `DELIMITER` and the usual comment forms. It does not support `SOURCE`, `\G`, `\.` or other client commands.
- No analytics, charts or web UI. (The submission's "simple analytics" requirement is outside this change.)
- No database provisioning. The CLI does not start Docker or MySQL. The existing `reset.sh` and the CI service container do that.
- No change to the SQL, the seed data, the Bash scripts or the Docker setup.
- Full SQL validation on Windows and macOS runners is not a goal (see Decision 7).

## Decisions

### 1. Package layout: `src/ie6700/` with a `pyproject.toml`, at the repository root

The project lives at the root of `IE6700-py`, not under `mysql/`. The SQL stays in `mysql/` and is located through one function that resolves `<repo root>/mysql` from the installed package's location, with an `IE6700_SQL_DIR` override.

- **Why:** the repo is the Python submission, so the root is where `README.md`, `.venv`, `.env` and `.github/` belong. The `src` layout stops tests from importing the working tree by accident, so the install check in CI means something.
- **Alternatives:** a flat module (simpler, but test imports can mask packaging errors); a project under `mysql/` (mixes tooling with the DB assets, and `.github/` must be at the root regardless).
- **Packaging detail:** because the SQL files are not part of the package, the install must be editable (`pip install -e .`) to find `mysql/`. If the package is installed non-editable and the SQL directory cannot be found, the CLI reports it and points to `IE6700_SQL_DIR`.

### 2. Driver: PyMySQL (pure Python)

- **Why:** no compiled extension, so `pip install` works the same on Windows, macOS and Linux with no compiler and no `libmysqlclient`. It supports MySQL 8 auth (`caching_sha2_password`, which needs the `cryptography` package for non-TLS password exchange, so `cryptography` is declared as a dependency; it ships wheels for all three OSes).
- **Alternatives:** `mysqlclient` (C extension, needs build tools on Windows); `mysql-connector-python` (pure Python and official, but heavier, and the C-extension/pure switch is a source of platform differences); shelling out to the `mysql` client (runs `DELIMITER` natively, but the client is not installed on Windows by default, which defeats the purpose).

### 3. Own SQL script splitter (`sqlscript.py`) instead of a library

A small state machine reads the text and yields `(start_line, statement_text)`. States: normal, single-quoted, double-quoted, backtick, `--` comment (a comment only when followed by whitespace, as MySQL requires), `#` comment, `/* */` comment. A line consisting of `DELIMITER <token>` outside a string changes the active delimiter and is not yielded. Statements are yielded without the delimiter. Empty or comment-only statements are dropped.

- **Why:** the syntax needed is small and fully specified by the course files. A splitter is pure and trivially unit-tested on every OS, with no database.
- **Alternatives:** `sqlparse.split` (does not handle `DELIMITER`, and splits some procedure bodies wrongly); `multi=True` execution (not supported by PyMySQL for procedures and loses per-statement line numbers); preprocessing the files to remove `DELIMITER` (changes the course files or requires a copy).
- **Conditional comments:** `/*! … */` and `/*+ … */` are passed to the server as part of the statement, not dropped, so version-conditional SQL keeps working.
- **Backslash escapes** inside strings are honoured (`\'`), with `''` treated as an escaped quote. `NO_BACKSLASH_ESCAPES` is not supported.

### 4. Execution model: one connection, one statement at a time

`runner.py` opens one connection per command run, with `charset=utf8mb4`, autocommit on, and no default database in the URL requirement (the scripts issue their own `USE`). It then executes each statement with `cursor.execute` and, after each statement, collects the result with `cursor.description` and `fetchall()`. For `CALL` statements it iterates `nextset()` so all result sets are captured.

- **Result record:** `ResultSet(file, line, title, columns, rows)`. `title` is the nearest preceding `-- N.N …` or `-- N. …` heading comment in the file, so the display can print "1.2 UC-1102 My listings…". The splitter exposes comments preceding a statement for this purpose.
- **Errors:** `pymysql.err.MySQLError` is wrapped as `SqlScriptError(file, line, errno, message, first_line_of_statement)`. The run stops. The connection closes, which also discards any open transaction.
- **Why one session:** `SET @x`, temporary tables and the `START TRANSACTION … ROLLBACK` blocks in the course files depend on it (see spec "One session per script run").
- **Value conversion:** `Decimal`, `date`, `datetime` and `bytes` are formatted by the renderer. JSON output uses strings for `Decimal` and ISO strings for dates, so no precision is lost.
- **Server check:** `load` first runs `SELECT VERSION()` and rejects non-8.x and MariaDB, matching `import_local.sh`.

### 5. Configuration (`config.py`)

`DATABASE_URL` is parsed with `urllib.parse`. `python-dotenv`'s `load_dotenv(override=False)` loads `.env`, which gives the "environment overrides file" rule for free. The search is `./.env`, then the repository root `.env`. A small frozen `Settings` dataclass has a `safe_url` property that masks the password, and every error path formats from it, never from the raw string. The CLI exit code for configuration problems is 2, for SQL and server problems 1.

- **Why a URL:** it is the single "connection string" the user asked for, it round-trips through a CI environment variable, and the password can be percent-encoded.
- **Alternative:** separate `DB_HOST`, `DB_PORT` variables (clearer to edit, but several values, and not a "connection string"). 

### 6. CLI (`cli.py`) and rendering (`render.py`)

`argparse` with subparsers, with no third-party CLI framework. `load`, `queries`, `test`, `status` are thin wrappers over the runner. `status` uses `information_schema` for table names and `COUNT(*)` per table for exact counts (`table_rows` is approximate in InnoDB, which would make CI assertions flaky).

- **Rendering:** `tabulate` with the `simple`/`github`-style plain table. It has no terminal-width detection, no colour and no wide-character magic, so output is identical on all OSes and is easy to compare in tests. Output streams are reconfigured to `utf-8` with `errors="replace"` at start-up, which avoids `UnicodeEncodeError` on legacy Windows consoles.
- **`--format csv|json`:** data to stdout, progress to stderr, so the output can be piped. The CI assertions use `--format json` and so do not parse human tables.
- **`rich`** was considered for nicer tables but its width detection and styling vary across terminals, and CI logs would then differ by platform.
- **`test` exit status** is derived from the data: it fails when any row of the delete-rule table has result `FAIL`, or the `failed` total is above 0, because the SQL itself always finishes with status 0.
- **`queries` display** prints the section heading and the row count of each result set. The health-check set is recognised by its header (`check`, `violations`), only in assertions, not in the display.

### 7. CI design: one real-database job on Linux, install checks on all three OSes

- **`sql-validation.yml` (ubuntu-latest):** a `mysql:8.4` service container with a health check (`mysqladmin ping`), `MYSQL_ROOT_PASSWORD` set to a throwaway value, port 3306 mapped. Steps: set up Python, create `.venv`, `pip install -e .[test]`, run `load`, `queries`, `test`, then `pytest tests/integration`. The integration tests call the library, load the database once, and compare results to `tests/expected/`.
- **`ci.yml` (matrix ubuntu, windows, macos):** create `.venv` with the platform's documented command (`python -m venv .venv`, then the OS-specific activation or directly `.venv/bin/python` / `.venv\Scripts\python.exe`), `pip install -e .[test]`, `ie6700 --help`, `python -m ie6700 --help`, `pytest tests` with the integration tests auto-skipped when `DATABASE_URL` is not set.
- **Why not MySQL on all three runners:** GitHub-hosted Windows and macOS runners cannot run Linux service containers. Installing MySQL there (`brew install mysql@8.4`, or the preinstalled Windows MySQL) is slow and version-fragile. The SQL is OS-independent, and what differs by OS is the Python side (venv, driver install, paths, line endings, console encoding), which the matrix covers.
- **CRLF coverage:** a unit test splits the SQL files read from disk and a copy converted to `CRLF`, and asserts the same statements. The matrix additionally runs on Windows' default `autocrlf` checkout.
- **Optional extension:** adding `brew install mysql@8.4` for the macOS leg is a reasonable follow-up if the Linux-only database job proves insufficient (see Open Questions).

### 8. Expected results (`tests/expected/`)

- `row_counts.json`: the exact row count for each of the 23 tables, captured from a known-good load. Update it by running a documented command in the same commit as a deliberate seed change.
- Delete rules: assertion by invariant (27 rows, all `PASS`, 0 failed) with no snapshot file, since the SQL already encodes pass/fail.
- Health checks: assertion by invariant (every `violations` equals 0, and the number of checks is at least the committed count in `row_counts.json`'s sibling `health_checks.json`, which lists check names). This catches a check being silently deleted.
- Queries: general assertion that every query ran and returned result sets, plus a small set of golden snapshots for deterministic aggregates (for example admin overview counts), kept few on purpose so they do not break on every seed edit.

### 9. Files left alone

`mysql/.env.example` and `mysql/.env` configure Docker and are unrelated. The new root `.env.example` points `DATABASE_URL` at the same sandbox (`mysql://root:ie6700_local_root@127.0.0.1:3307/seattle_marketplace`), so `./mysql/reset.sh` followed by `ie6700 load` works with no edits. Because `marketplace.sql` has `CREATE DATABASE IF NOT EXISTS`, the database path in the URL is only a default and does not need to exist at connect time (the tool connects without selecting a database for `load` and selects it after).

### Code Change Inventory

| File Path | Change Type | Change Description | Affected Module |
| --- | --- | --- | --- |
| `pyproject.toml` | Add | Metadata, `requires-python >=3.10`, dependencies (`PyMySQL`, `cryptography`, `python-dotenv`, `tabulate`), optional `test` extra (`pytest`), `[project.scripts] ie6700 = "ie6700.cli:main"`, setuptools config for the `src` layout | Packaging |
| `src/ie6700/__init__.py` | Add | `__version__` | Package |
| `src/ie6700/__main__.py` | Add | Calls `cli.main()` so `python -m ie6700` works | CLI entry |
| `src/ie6700/paths.py` | Add | `sql_dir()` with `IE6700_SQL_DIR` override, `LOAD_SEQUENCE`, `QUERIES_FILE`, `DELETE_RULES_FILE` constants | Path resolution |
| `src/ie6700/config.py` | Add | `Settings`, `load_settings()`, `.env` search, URL validation, `safe_url` masking, `ConfigError` | Configuration |
| `src/ie6700/sqlscript.py` | Add | `split_script(text) -> Iterator[Statement]` with line numbers, `DELIMITER`, comments and quotes; heading-comment capture | SQL parsing |
| `src/ie6700/db.py` | Add | `connect(settings)`, server version check, `table_counts()` helpers | Database access |
| `src/ie6700/runner.py` | Add | `run_script(conn, path) -> list[ResultSet]`, `SqlScriptError`, multi-result `CALL` handling | SQL execution |
| `src/ie6700/render.py` | Add | Table, CSV and JSON renderers, value formatting, UTF-8 stdout setup | Display |
| `src/ie6700/cli.py` | Add | `argparse` subcommands, exit codes, `load` table-count verification, `test` result evaluation | CLI |
| `.env.example` | Add | `DATABASE_URL` default for the local sandbox, with comments | Configuration |
| `.gitignore` | Add | `.venv/`, `.env`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `build/`, `dist/` | Repository hygiene |
| `README.md` | Modify | Keep submission requirements; add Setup (Linux/macOS, PowerShell, cmd), Configure, Usage and Troubleshooting sections | Documentation |
| `tests/conftest.py` | Add | Fixtures: settings from environment, skip integration tests without `DATABASE_URL`, one-time `load` | Tests |
| `tests/test_config.py` | Add | URL parsing, defaults, encoding, precedence, masking, error messages | Tests |
| `tests/test_sqlscript.py` | Add | Splitter cases, CRLF equality, splitting each real `mysql/*.sql` file with no empty or unterminated statement | Tests |
| `tests/test_render.py` | Add | Table, CSV, JSON formatting, `NULL`, `Decimal`, dates | Tests |
| `tests/test_cli.py` | Add | Help output, unknown command status 2, missing config status 2, no password in output | Tests |
| `tests/integration/test_course_sql.py` | Add | Load, table count, row counts, delete-rule outcome, health-check invariants, queries run | Tests, CI |
| `tests/expected/row_counts.json` | Add | Expected rows per table | Tests, CI |
| `tests/expected/health_checks.json` | Add | Expected health-check names | Tests, CI |
| `tests/expected/statement_counts.json` | Add | Statement count per course SQL file, to guard the splitter | Tests |
| `tests/test_paths.py` | Add | SQL directory resolution and override | Tests |
| `.github/workflows/ci.yml` | Add | Matrix venv install and unit tests | CI |
| `.github/workflows/sql-validation.yml` | Add | MySQL 8.4 service container and the integration run | CI |

## Risks / Trade-offs

- **Splitter diverges from the real `mysql` client on an edge case** → The course files are the only input. A test splits every real file and checks the output against an independent signal (the number of statements the Bash path would send, counted once and committed), and the integration run executes them for real.
- **`DELIMITER` handling hides a real bug in `delete_rules.sql`** → Run `delete_rules.sql` through both the Bash path and the Python path during implementation and compare the PASS/FAIL table.
- **Seed row counts are a brittle snapshot** → Counts live in one reviewable JSON file, and the failure message names the table and both counts. Updating it is part of changing seed data.
- **Real-database CI only on Linux** → Windows and macOS legs cover the Python side only. A Windows-specific database difference is unlikely because the server is the same, but it is not proven. Mitigation: documented in the README, and an extension is listed under Open Questions.
- **`cryptography` wheel availability on new Python versions** → Pin a lower bound only, test the matrix on the Python versions supported (3.10 to latest), and keep `requires-python` honest.
- **Editable-install requirement for finding `mysql/`** → The README says to use `pip install -e .`. The CLI reports a clear message and `IE6700_SQL_DIR` as an escape hatch.
- **`caching_sha2_password` over a non-TLS local connection** → PyMySQL needs `cryptography` and RSA key exchange, which MySQL 8.4 supports for root. Covered by the integration job on the real 8.4 image.
- **`queries` section 6 writes leave traces** → They run inside `START TRANSACTION … ROLLBACK`, so rows are unchanged, but auto-increment counters advance (as the existing README notes). Row-count assertions run before `queries`.
- **`load` is not idempotent** → Same as `db.sh load`. Documented and reported with a hint to reset. A `--drop-existing` option is deliberately left out to keep destructive actions out of this change.

## Migration Plan

Additive change in one repository, with nothing to migrate.

1. Add the package, tests and documentation.
2. Verify locally against the Docker sandbox: `./mysql/reset.sh`, then `ie6700 load`, `queries`, `test`, comparing `test` with `./mysql/db.sh test`.
3. Add the workflows. Both only report status.

Rollback: remove the new files. The `mysql/` directory and the Bash workflow are unchanged, so the previous way of working is unaffected.

## Open Questions

- Whether to also run the full SQL validation on a macOS runner with a Homebrew MySQL 8.4 once the Linux job is stable. It can be added without changing the specs.
- The minimum supported Python (3.10 is assumed) and which versions the matrix covers. This can be tuned without changing the specs.
