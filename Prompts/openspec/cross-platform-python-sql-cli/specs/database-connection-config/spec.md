# Spec Delta

## Purpose

Defines how the tool learns where the database is: one connection string read from `.env` or the environment, checked up front, and never printed with its password.

## ADDED Requirements

### Requirement: Connection string from .env
The tool SHALL read one connection string named `DATABASE_URL` in the form `mysql://user:password@host:port/database`. It SHALL load a `.env` file from the current working directory, or from the repository root when none is there. The repository SHALL provide `.env.example` with a working local default pointing at the existing Docker sandbox (`127.0.0.1:3307`, database `seattle_marketplace`).

#### Scenario: Value read from .env
- **WHEN** `.env` contains `DATABASE_URL=mysql://root:secret@127.0.0.1:3307/seattle_marketplace` and the variable is not set in the environment
- **THEN** the tool connects to host `127.0.0.1`, port `3307`, as user `root`, using database `seattle_marketplace`

#### Scenario: Default port and URL-encoded password
- **WHEN** `DATABASE_URL` omits the port and the password contains `%40` for `@`
- **THEN** port 3306 is used and the password is decoded to contain `@`

### Requirement: Environment overrides the file
A `DATABASE_URL` set in the process environment SHALL take precedence over the value in `.env`.

#### Scenario: CI-style override
- **WHEN** `.env` and the environment both define `DATABASE_URL` with different hosts
- **THEN** the tool uses the host from the environment

### Requirement: Fail early on missing or malformed configuration
When `DATABASE_URL` is missing or cannot be parsed, the CLI SHALL exit with status 2 before contacting any database. The message SHALL say whether it is missing or malformed and point to `.env.example`. It SHALL NOT include the password.

#### Scenario: No configuration
- **WHEN** neither `.env` nor the environment defines `DATABASE_URL`
- **THEN** the CLI exits with status 2 and tells the user to copy `.env.example` to `.env`

#### Scenario: Unsupported scheme
- **WHEN** `DATABASE_URL` starts with `postgres://`
- **THEN** the CLI exits with status 2 and states that only `mysql://` is supported

### Requirement: Secrets are never displayed
Every message the tool prints, including connection errors, SQL errors and verbose output, SHALL show the password only as `***`.

#### Scenario: Connection refused
- **WHEN** the server is unreachable and the URL contains the password `secret`
- **THEN** the printed error names the host and port, contains `***` in place of the password, and does not contain the text `secret`
