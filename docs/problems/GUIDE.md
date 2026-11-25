# How to Implement and Verify a Problem

Each problem is one SQL query plus a small amount of Python analysis. The problem file states the question and the data needed; you write the SQL in the module. The reference implementations are `src/ie6700/analytics/p1_search_and_price.py` and `p4_pickup_and_cross_campus.py`, with their tests. Shared requirements are in [README.md](README.md).

## 1. Steps

1. **Start the sandbox.** From the `IE6700-py` folder:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   python -m pip install -e ".[test]"
   cp .env.example .env
   ./mysql/reset.sh --load        # fresh MySQL 8.4 with the seed data
   ```

2. **Draft the query in a client.** Run it in `cd mysql && ./db.sh shell` with `NULL` or sample values in place of each `%s`, and confirm the output matches section 4 of the problem file. If it does not, find out whether the query or the file is wrong; do not bend the code to match a wrong number.
3. **Write the module** `src/ie6700/analytics/pN_<name>.py` (section 2), with the query as one constant.
4. **Write the tests** (section 3).
5. **Run and finish** (section 4).

## 2. The Module

Keep three small parts:

| Part | Content |
| --- | --- |
| SQL constant | The one query, with `%s` placeholders and a comment saying what each row is |
| `fetch_*` function | Runs it with bound parameters and returns plain Python values |
| Analysis and `main` | Pure functions that compute the metrics, then printing and exit status |

Use `analytics/common.py`: `run_with_connection` (connection, version check, exit statuses, no password in output), `InvalidInput` (bad argument, status 2), `money()`, `percent()` (prints `-` for a zero denominator), and `print_table()`.

Rules:

1. Every user value goes through `cur.execute(sql, params)`; no string-built SQL.
2. `SELECT` only; never touch `mysql/`.
3. Compute the metrics in Python from the returned rows. Use `Decimal` for money.
4. `ORDER BY` must have a tie-breaker so output is deterministic.
5. Bad input prints one `error:` line on standard error and exits non-zero.

Skeleton:

```python
SQL = """..."""  # the one query for this problem

def fetch(conn, seller_id):
    with conn.cursor() as cur:
        cur.execute(SQL, (seller_id, seller_id))
        return cur.fetchall()

def main(argv=None):
    args = build_parser().parse_args(argv)
    return run_with_connection(lambda conn: report(conn, args.seller))
```

## 3. The Tests

| File | Database | Covers |
| --- | --- | --- |
| `tests/test_analytics_pure.py` | not needed | The analysis functions on small hand-made rows, zero denominators, argument errors and exit statuses |
| `tests/integration/test_analytics.py` | needed (skipped without `DATABASE_URL`) | Every number in sections 4 and 5 of the problem file, against the seeded sandbox |

For the integration test, write one assertion per expected number and copy the number from the problem file, so a change on either side fails the test. Add two guard tests per module:

- **Read-only**: compare `db.table_counts(conn, COURSE_SCHEMA)` before and after running the report.
- **Bound parameters**: pass a value such as `"'; DROP TABLE Campus; --"` as a filter and check that it returns no rows and the tables still exist.

## 4. Run and Finish

```bash
python -m pytest tests                    # unit tests; integration tests are skipped without a database
python -m pytest tests/integration -v     # needs the loaded sandbox
python -m ie6700.analytics.<module>       # run the application by hand
```

Before opening a pull request:

- [ ] The printed output shows the numbers from section 4 of the problem file.
- [ ] The module runs only the one query (a `WITH`/`SELECT` with no `;`), with `%s` placeholders and no concatenated input.
- [ ] Error paths behave as the problem file says.
- [ ] Unit tests pass without a database and integration tests pass on a freshly reset sandbox.
- [ ] `git status` shows no change under `mysql/`.
- [ ] The status in the problem file and in the table in [README.md](README.md) is updated.

CI runs the unit tests on Linux, Windows, and macOS (Python 3.10 and 3.13) without a database, and runs the integration tests against MySQL 8.4 in `sql-validation.yml`.

If the seed data changes on purpose, re-run each problem's query (in the module), update the expected numbers and tests in the same commit, and update the baseline date in [README.md](README.md).
