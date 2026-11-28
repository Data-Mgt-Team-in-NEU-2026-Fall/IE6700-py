# Spec Delta

## Purpose

Defines how `.sql` script files written for the `mysql` command-line client are executed unchanged by the tool, with the same statement semantics and clear failure reporting, on every supported operating system.

## ADDED Requirements

### Requirement: Client-style script syntax
The executor SHALL run a script statement by statement and SHALL understand `DELIMITER` directives, `--` line comments, `/* */` block comments, and semicolons or delimiter characters inside quoted strings and comments. A `DELIMITER //` block containing `CREATE PROCEDURE` with inner semicolons SHALL be sent as one statement.

#### Scenario: Stored procedure with inner semicolons
- **WHEN** a script contains `DELIMITER //`, a `CREATE PROCEDURE` body with several `;` and then `DELIMITER ;`
- **THEN** the procedure is created as a single statement and the later statements run with `;` as the delimiter

#### Scenario: Semicolon in a string or comment
- **WHEN** a statement contains `'a;b'` or a comment containing `;`
- **THEN** it is not split at that semicolon

### Requirement: One session per script run
All statements of one run SHALL execute in one database session, so `USE`, `SET @variable`, temporary tables, `START TRANSACTION` and `ROLLBACK` behave as in the `mysql` client. Autocommit SHALL be on unless the script itself starts a transaction.

#### Scenario: Parameters set at the top of a script
- **WHEN** `queries.sql` sets `@variable` values in its first statements
- **THEN** later queries in the same run use those values

#### Scenario: Rolled-back writes
- **WHEN** a script updates rows inside `START TRANSACTION … ROLLBACK`
- **THEN** the table contents after the run equal those before it

### Requirement: Result sets are captured in order
Every statement that returns rows SHALL produce a result set holding its column names and rows, kept in script order and linked to the file and line where its statement starts. Statements that return no rows SHALL produce no result set.

#### Scenario: Two queries in one file
- **WHEN** a script has two `SELECT` statements and one `INSERT`
- **THEN** two result sets are returned, in script order, each with its start line

#### Scenario: Stored procedure result sets
- **WHEN** a statement is a `CALL` that returns more than one result set
- **THEN** each of them is captured in the order the server returns it

### Requirement: Fail fast with a precise location
On the first SQL error the executor SHALL stop, run no later statement, and report the file, the line where the failing statement starts, the server error number and message, and the first line of the statement. The CLI SHALL exit with status 1.

#### Scenario: Syntax error mid-file
- **WHEN** the third statement of a script is invalid
- **THEN** the first two statements have run, the rest have not, and the report names the file, the third statement's start line and the server error

### Requirement: Course file order and encoding
Files SHALL be read as UTF-8 with or without a byte-order mark and with `LF` or `CRLF` line endings. The `load` sequence SHALL run `marketplace.sql`, then `seed/01_identity.sql`, `seed/02_marketplace.sql` and `seed/03_messaging_reviews_reports.sql`, in that order.

#### Scenario: CRLF checkout on Windows
- **WHEN** the SQL files are checked out with `CRLF` line endings
- **THEN** the results of every statement are the same as with `LF` endings

#### Scenario: Repeated load
- **WHEN** `load` runs against a server where `seattle_marketplace` already has tables
- **THEN** the run stops at the first conflicting statement with an error, as the existing scripts do, and tells the user to reset the database first
