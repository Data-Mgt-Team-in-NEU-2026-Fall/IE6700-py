# Spec Delta

## Purpose

Defines how a user installs and starts the course SQL tool in a project-local `.venv` on Windows, macOS and Linux, with no system-wide installation and no compiler or database client library.

## ADDED Requirements

### Requirement: Installable into a project-local virtual environment
The project SHALL be installable with `pip` into a `.venv` directory at the repository root. After installation, the `ie6700` command and `python -m ie6700` SHALL both start the CLI. Installation SHALL NOT require a C compiler, a system MySQL client library or administrator rights.

#### Scenario: Fresh install on any supported OS
- **WHEN** a user creates `.venv`, activates it and installs the project on Windows, macOS or Linux
- **THEN** both `ie6700 --help` and `python -m ie6700 --help` print the command list and exit with status 0

#### Scenario: Unsupported Python version
- **WHEN** a user installs the project with a Python older than the documented minimum
- **THEN** installation fails with a message that names the required Python version

### Requirement: Per-platform setup documentation
The repository `README.md` SHALL give copy-paste commands to create, activate and use `.venv` for Linux and macOS (bash/zsh), Windows PowerShell and Windows cmd. It SHALL also cover installing the project, copying `.env.example` to `.env`, and running each CLI command.

#### Scenario: Windows user follows the README
- **WHEN** a Windows user follows the PowerShell instructions in order
- **THEN** each command is given verbatim, including the activation script path for PowerShell, and no step needs a Unix-only tool

#### Scenario: Existing submission requirements are kept
- **WHEN** the README is updated for this setup
- **THEN** the Project Submission Requirements section is still present and unchanged

### Requirement: Local files stay out of version control
The repository SHALL ignore `.venv/`, `.env`, Python caches and build output, and SHALL NOT ignore `.env.example`.

#### Scenario: Secrets are not tracked
- **WHEN** a user creates `.env` with a real password and checks the working tree status
- **THEN** `.env` is not listed as an untracked file

### Requirement: Setup does not change course SQL assets
Installing or running the project SHALL NOT modify any file under `mysql/`.

#### Scenario: Files unchanged after a full run
- **WHEN** a user runs `load`, `queries` and `test` once
- **THEN** every file under `mysql/` is byte-identical to before
