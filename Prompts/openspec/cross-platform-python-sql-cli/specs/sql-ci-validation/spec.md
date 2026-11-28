# Spec Delta

## Purpose

Defines the automated checks that run in GitHub Actions to prove that the course SQL still loads, returns the expected results, and that the Python setup works on Windows, macOS and Linux.

## ADDED Requirements

### Requirement: SQL validation workflow
A GitHub Actions workflow SHALL run on every push and pull request. It SHALL start a MySQL 8.4 server, install the project into a fresh `.venv`, run `load`, `queries` and `test` through the CLI, and fail if any of them exits with a non-zero status.

#### Scenario: Healthy repository
- **WHEN** the workflow runs on a commit where the SQL files are correct
- **THEN** all three CLI commands exit with status 0 and the job succeeds

#### Scenario: Broken SQL
- **WHEN** a commit introduces a syntax error in `mysql/queries.sql`
- **THEN** the job fails and its log shows the file, line and server error

### Requirement: Expected result assertions
The workflow SHALL assert the results themselves, not only that the commands ran: exactly 23 base tables, the committed row count for every table, 27 delete-rule rows all `PASS` with 0 failed, and 0 in the violations column of every data-health check in `queries.sql`.

#### Scenario: Seed data changes unexpectedly
- **WHEN** a seed file loses or gains rows so a table's count differs from the committed expectation
- **THEN** the assertion fails and names the table, the expected count and the actual count

#### Scenario: Data-health check finds a violation
- **WHEN** a health check returns a violation count above 0
- **THEN** the assertion fails and names that check

### Requirement: Expected values are reviewable and updatable
The expected row counts and other fixed expectations SHALL be stored as text files in the repository, so a deliberate change to seed data is visible in a diff.

#### Scenario: Intentional seed update
- **WHEN** a maintainer adds seed rows and updates the expectation files in the same commit
- **THEN** the workflow passes without any other change

### Requirement: Cross-platform install check
A second workflow SHALL run on `ubuntu-latest`, `windows-latest` and `macos-latest`. On each it SHALL create `.venv` with the platform's documented commands, install the project, run `ie6700 --help` and `python -m ie6700 --help`, and run the unit tests.

#### Scenario: Windows runner
- **WHEN** the workflow runs on `windows-latest`
- **THEN** `.venv` is created and activated using the Windows commands, the CLI starts and the unit tests pass

#### Scenario: Unit tests need no database
- **WHEN** the unit tests run on a runner without a MySQL server
- **THEN** they pass, and the tests that need a server are skipped, not failed

### Requirement: Deterministic and secret-free runs
Workflows SHALL pin the MySQL image to a major.minor version, pass the connection string only through the job environment with a throwaway password, and SHALL NOT use repository secrets.

#### Scenario: Fork pull request
- **WHEN** a pull request comes from a fork with no access to secrets
- **THEN** the validation workflow still runs to completion
