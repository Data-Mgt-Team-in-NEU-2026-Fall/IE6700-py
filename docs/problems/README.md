# Course Application Problems (MySQL Data Analysis)

Course requirement: build a Python application that connects to a MySQL database, embeds at least 3 queries that retrieve data, and performs simple analysis on the retrieved data. Modeling is not required. All problems are implemented in Python (PyMySQL); R is not used.

Six problems are given here, and each person owns 2. Every problem states its design goals and expected results, and the expected results are based on the seed data loaded by `ie6700 load`. Problem files follow [TEMPLATE.md](TEMPLATE.md). The template is kept so that new problems can use it later.

To implement and verify a problem, follow [GUIDE.md](GUIDE.md).

## Problems and Assignments

The assignments are suggestions and can be edited directly in the table below.

| ID | Problem | Subsystems involved | Owner | Status |
| --- | --- | --- | --- | --- |
| [P1](P1-search-and-price.md) | Item search and price overview | Items and discovery | Kun Yu | Not started |
| [P2](P2-seller-report.md) | Seller performance report | Items, transactions, reviews | Eduardo Gonzalez | Implemented (in review) |
| [P3](P3-request-funnel.md) | Purchase request conversion funnel | Purchase requests, orders | Yuan Xia | Not started |
| [P4](P4-pickup-and-cross-campus.md) | Pickup points and cross-campus transactions | Pickup points, campuses | Kun Yu | Not started |
| [P5](P5-messaging-activity.md) | Conversation and message activity | Messaging | Eduardo Gonzalez | Implemented (in review) |
| [P6](P6-trust-and-safety.md) | Trust analysis of reviews and reports | Reviews, reports | Yuan Xia | Not started |

## Requirements Shared by All Problems

1. **One complex query per problem**: each problem is built around a single, parameterized `SELECT` (CTEs, joins, window functions or aggregates as needed). The problem files only state the problem and the data needed; the owner writes the SQL in the Python module. Parameters use PyMySQL `%s`; never concatenate user input. The course requirement of at least 3 embedded queries is met by the project as a whole (6 problems, 6 queries), and each owner's two problems give two.
2. **Analysis in Python**: the query returns summary rows, and Python computes the problem's metrics from them (ratios, averages, rankings). Printing raw rows alone is not enough.
3. **Read-only**: only `SELECT`; never modify the database or any file under `mysql/`.
4. **No modeling**: simple statistics only.
5. **Connection configuration**: reuse the `ie6700` configuration (`DATABASE_URL`, see the repository README). Code goes in `src/ie6700/analytics/`, one module per problem.
6. **Verified expectations**: every number in a problem file was checked on the sandbox with SQL. The owner re-checks it with the module's own query, and the integration tests assert it.
7. **Relationship to `queries.sql`**: `mysql/queries.sql` belongs to the MySQL milestone. Consult it if useful, but write the application's query yourself and do not call that file.

## Data Baseline

The expected numbers were verified on the sandbox on 2026-11-24 (after `./mysql/reset.sh --load`, the 23 tables of `seattle_marketplace`). If the seed data changes, the expected numbers in the problem files must be updated as well.
