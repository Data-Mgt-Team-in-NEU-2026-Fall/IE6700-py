# Spec Delta

## Purpose

Defines the command-line interface through which a user loads the course database, runs the course queries and delete-rule tests, and reads the results as text tables with reliable exit codes.

## ADDED Requirements

### Requirement: Command set
The CLI SHALL provide the subcommands `load`, `queries`, `test` and `status`, and `--help` for the program and each subcommand. An unknown subcommand or option SHALL exit with status 2 and print usage.

#### Scenario: Help lists all commands
- **WHEN** a user runs `ie6700 --help`
- **THEN** the output lists `load`, `queries`, `test` and `status` with a one-line description each

#### Scenario: Unknown command
- **WHEN** a user runs `ie6700 frobnicate`
- **THEN** the CLI prints usage and exits with status 2

### Requirement: load command
`load` SHALL execute `mysql/marketplace.sql` and the three seed files in order against the configured server, and then verify that `seattle_marketplace` has exactly 23 base tables. It SHALL print each file name with `ok` as it completes, and exit with status 0 only if every file ran and the table count is 23.

#### Scenario: Load into an empty server
- **WHEN** `load` runs against an empty MySQL 8.x server
- **THEN** it prints four `ok` lines, reports 23 tables, and exits with status 0

#### Scenario: Server is not MySQL 8
- **WHEN** the server version starts with something other than `8.` or reports MariaDB
- **THEN** `load` stops before running any file, explains that MySQL 8.x is required, and exits with status 1

### Requirement: queries command
`queries` SHALL run `mysql/queries.sql` and print every result set as a text table, preceded by the number and the heading comment of its query when the file provides one. It SHALL print each query's row count and exit with status 0 when the whole file ran.

#### Scenario: Tables displayed
- **WHEN** `queries` runs against a loaded database
- **THEN** each query's rows appear as an aligned table with a header row and the last table is the data-health check

#### Scenario: Database not loaded
- **WHEN** `queries` runs against a server where `seattle_marketplace` does not exist
- **THEN** it exits with status 1 and tells the user to run `load` first

### Requirement: test command
`test` SHALL run `mysql/delete_rules.sql`, print its PASS/FAIL table and its totals, and exit with status 0 only when every rule is PASS and the failed total is 0.

#### Scenario: All rules pass
- **WHEN** `test` runs against a freshly loaded database
- **THEN** it shows 27 rows with `PASS`, a totals row of 27 passed and 0 failed, and exits with status 0

#### Scenario: A rule fails
- **WHEN** at least one rule row shows `FAIL`
- **THEN** the table is still printed in full and the exit status is 1

### Requirement: status command
`status` SHALL print the server version, character set and collation, and each table in `seattle_marketplace` with its exact row count, then exit with status 0.

#### Scenario: Row counts after load
- **WHEN** `status` runs after a successful `load`
- **THEN** it lists 23 tables, each with an exact row count taken with `COUNT(*)`

### Requirement: Display is portable and scriptable
Tables SHALL be printed as plain Unicode-safe text that does not depend on terminal width detection or colour. `NULL` SHALL be shown as `NULL`. Option `--format` SHALL accept `table` (default), `csv` and `json`, and for `csv` and `json` only result data SHALL go to standard output while progress goes to standard error.

#### Scenario: Machine-readable output
- **WHEN** a user runs `ie6700 queries --format json`
- **THEN** standard output is a single valid JSON document with every result set and nothing else

#### Scenario: Legacy Windows console
- **WHEN** the CLI prints text on a Windows console whose default encoding is not UTF-8
- **THEN** it does not crash with an encoding error
