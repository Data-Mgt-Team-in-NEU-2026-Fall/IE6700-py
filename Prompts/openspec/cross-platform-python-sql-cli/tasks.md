# Tasks

All paths are relative to `repos/IE6700-py`. Files under `mysql/` are read only and MUST NOT be modified.

## 1. Project scaffolding

- [x] 1.1 Add `pyproject.toml` (`src` layout, `requires-python >=3.10`, dependencies `PyMySQL`, `cryptography`, `python-dotenv`, `tabulate`, a `test` extra with `pytest`, console script `ie6700 = ie6700.cli:main`). Verify with `python -m venv .venv && .venv/bin/pip install -e ".[test]"` succeeding in a clean checkout.
- [x] 1.2 Add `.gitignore` (`.venv/`, `.env`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `build/`, `dist/`) and verify `git status` does not list a freshly created `.venv/` or `.env`, while `.env.example` is not ignored.
- [x] 1.3 Add `src/ie6700/__init__.py` (`__version__`) and `src/ie6700/__main__.py`, plus a stub `cli.main()` that handles `--help`. Verify `ie6700 --help` and `python -m ie6700 --help` both exit 0.
- [x] 1.4 Add `src/ie6700/paths.py` (`sql_dir()` resolving `<repo>/mysql`, `IE6700_SQL_DIR` override, the `load` file sequence, queries and delete-rules constants, clear error when the directory is missing). Verify with a unit test in `tests/test_paths.py` that covers the default, the override and the missing-directory message, and that the four load files, `queries.sql` and `delete_rules.sql` all resolve to existing files.

## 2. Connection configuration

- [x] 2.1 Implement `src/ie6700/config.py` (`Settings`, `load_settings()`, `.env` search in the working directory then the repository root, `DATABASE_URL` parsing with default port 3306 and percent-decoding, `mysql://` only, `safe_url` password masking, `ConfigError`). Verify with `tests/test_config.py` for: value read from `.env`, environment overriding `.env`, default port, encoded password, missing value, malformed value, wrong scheme.
- [x] 2.2 Make the CLI report `ConfigError` before any connection attempt with exit status 2 and a pointer to `.env.example`. Verify with `tests/test_cli.py`: no configuration gives status 2 with the hint, and a configured URL with password `secret` never prints `secret` in the output of a failing connection.
- [x] 2.3 Add `.env.example` with `DATABASE_URL=mysql://root:ie6700_local_root@127.0.0.1:3307/seattle_marketplace` and short comments. Verify by parsing the file with `load_settings()` in a unit test and checking it yields host `127.0.0.1`, port `3307`.

## 3. SQL script splitter

- [x] 3.1 Implement `src/ie6700/sqlscript.py` (`split_script` yielding statements with start line and preceding heading comment; `DELIMITER` changes; `--`, `#` and `/* */` comments; single, double and backtick quotes with escapes; conditional comments passed through; `CRLF` and a UTF-8 byte-order mark accepted). Verify with `tests/test_sqlscript.py` covering each case in the `sql-script-execution` spec: procedure body with inner semicolons, semicolon in a string, semicolon in a comment, `--` without a following space, CRLF equal to LF, comment-only chunks dropped.
- [x] 3.2 Add a test that splits every real file (`marketplace.sql`, the three seed files, `queries.sql`, `delete_rules.sql`) and checks that no statement is empty, no statement contains a bare `DELIMITER` line, and the statement count equals the count committed in `tests/expected/statement_counts.json` (generated once from the implementation and cross-checked against the `mysql` client's behaviour on the sandbox). Verify the test passes without a database.

## 4. Execution and display

- [x] 4.1 Implement `src/ie6700/db.py` (connect with `utf8mb4`, autocommit on, server version check that rejects MariaDB and non-8.x, exact `COUNT(*)` table counts helper). Verify with a unit test of the version check (fake version strings) and an integration test, skipped without `DATABASE_URL`, that connects to the sandbox.
- [x] 4.2 Implement `src/ie6700/runner.py` (`run_script`, one session, result-set capture in order including `CALL` with several result sets, `SqlScriptError` with file, line, error number, message and first statement line, stop on first error). Verify with an integration test that runs a temporary script containing `SET @x`, a `SELECT @x`, a procedure created under `DELIMITER //`, and a deliberate error on a known line, and asserts the captured sets and the reported location.
- [x] 4.3 Implement `src/ie6700/render.py` (plain text table, CSV, JSON; `NULL`; `Decimal`, date and datetime formatting; UTF-8 output with `errors="replace"`). Verify with `tests/test_render.py` including a case that writes non-ASCII text to a stream whose encoding is `cp1252`.

## 5. CLI commands

- [x] 5.1 Implement `load` in `src/ie6700/cli.py` (version check, run `marketplace.sql` then the three seed files, print one `ok` line per file, verify 23 base tables, status 0 only on success, hint to reset on "already exists" errors). Verify by running it against an empty `mysql:8.4` container and then again to see the hint and status 1.
- [x] 5.2 Implement `queries` (all result sets printed with section headings and row counts; message and status 1 when `seattle_marketplace` is missing). Verify against a loaded sandbox that the output contains every section of `queries.sql`, and against an empty server for the message.
- [x] 5.3 Implement `test` (print the PASS/FAIL table and totals; exit 0 only when no row is `FAIL` and failed total is 0). Verify with a loaded sandbox (27 `PASS`, status 0), and with a unit test that feeds a result set containing one `FAIL` and expects status 1. Also compare the table with `./mysql/db.sh test` on the same sandbox.
- [x] 5.4 Implement `status` (version, character set, collation, exact row count per table). Verify that after `load` it lists 23 tables and the counts match `tests/expected/row_counts.json`.
- [x] 5.5 Implement `--format table|csv|json` for the commands that print results, sending progress to standard error. Verify with `tests/test_cli.py` that `queries --format json` writes one valid JSON document to standard output and nothing else, and that unknown commands print usage and exit 2.

## 6. Expected results and integration tests

- [x] 6.1 Capture `tests/expected/row_counts.json` (rows per table) and `tests/expected/health_checks.json` (names of the data-health checks in `queries.sql` section 8) from a known-good load. Verify by diffing against `./mysql/db.sh status` and the section 8 query output on the Docker sandbox.
- [x] 6.2 Add `tests/conftest.py` and `tests/integration/test_course_sql.py`: load once per session, then assert 23 tables, row counts equal the expected file (failure message names table, expected and actual), 27 delete-rule rows all `PASS` with 0 failed, every health-check `violations` equals 0 and every expected check is present, and `queries.sql` runs end to end. Verify the whole suite passes against the sandbox and that the integration tests are skipped, not failed, when `DATABASE_URL` is unset.
- [x] 6.3 Verify the assertions detect problems by temporarily running the suite against a copy of the data with one deleted seed row and a copy of `queries.sql` with a syntax error (via `IE6700_SQL_DIR` pointing at a temporary directory), and checking that both fail with the documented messages. Do not change files under `mysql/`.

## 7. GitHub Actions

- [x] 7.1 Add `.github/workflows/sql-validation.yml`: triggers on push and pull request; `ubuntu-latest`; `mysql:8.4` service container with a health check and throwaway root password; create `.venv`, `pip install -e ".[test]"`, run `ie6700 load`, `queries`, `test`, then `pytest tests/integration`; connection string only through the job environment, no repository secrets. Verify the YAML with `actionlint` (or a YAML parser if `actionlint` is unavailable) and by running the same steps locally against a `mysql:8.4` container.
- [x] 7.2 Add `.github/workflows/ci.yml`: matrix `ubuntu-latest`, `windows-latest`, `macos-latest` with the supported Python versions; create `.venv` using each platform's documented commands; install, run `ie6700 --help`, `python -m ie6700 --help` and `pytest tests` (integration tests skipped without a database). Verify the YAML as in 7.1, and verify locally that the unit test suite passes with `DATABASE_URL` unset.

## 8. Documentation and final checks

- [x] 8.1 Update `README.md`: keep the Project Submission Requirements section unchanged and add Setup (create, activate and use `.venv` for Linux/macOS, Windows PowerShell and Windows cmd, install, `.env` creation), Configure (`DATABASE_URL`, how to start the Docker sandbox with `./mysql/reset.sh`), Usage (`load`, `queries`, `test`, `status`, `--format`) and Troubleshooting (missing config, MariaDB or non-8.x, "already exists", `IE6700_SQL_DIR`). Verify by following the Linux commands from a clean clone, and that every command shown in the README exists in `--help`.
- [x] 8.2 Run the full local check: fresh `.venv`, `pip install -e ".[test]"`, `./mysql/reset.sh`, `ie6700 load`, `ie6700 queries`, `ie6700 test`, `ie6700 status`, `pytest tests`. Verify that every command exits 0 and `git status` shows no change under `mysql/`.
