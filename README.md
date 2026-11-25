# IE6700-py

## Project Submission Requirements

Submit your project implementation of an application in Python or R. The submission must meet the following requirements:

1. An application is created in Python or R, which accesses your MySQL database.
2. At least 3 queries are embedded in the application, which retrieve data from the MySQL database.
3. Simple analytics are built based on the retrieved data. Modeling is not required.

Additional submission rules:

- Include the cover page (see the project guideline).
- Follow the project guideline.

## What this project does

`ie6700` is a small Python tool that runs the course SQL files in `mysql/` unchanged:

- `load` creates the `seattle_marketplace` database from `mysql/marketplace.sql` and the three seed files.
- `queries` runs `mysql/queries.sql` and prints each result set.
- `test` runs the delete-rule tests in `mysql/delete_rules.sql` and prints the PASS/FAIL table.
- `status` prints the server version and the row count of each table.

It needs Python 3.10 or later and a MySQL 8.x server. It does not need Docker, Bash or the `mysql` client; Docker is only used to start the local sandbox.

## Setup

Create a project-local virtual environment in the repository root and install the project into it. Run these commands from the `IE6700-py` folder.

### Linux and macOS (bash or zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
cp .env.example .env
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
Copy-Item .env.example .env
```

### Windows cmd

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
copy .env.example .env
```

Once the environment is active, `ie6700` and `python -m ie6700` are available. Without activating, run `.venv/bin/ie6700` (Linux and macOS) or `.venv\Scripts\ie6700.exe` (Windows).

## Configure

The only setting is `DATABASE_URL`, in the form `mysql://user:password@host:port/database`:

```text
DATABASE_URL=mysql://root:ie6700_local_root@127.0.0.1:3307/seattle_marketplace
```

- The command reads `.env` from the current folder, or from the repository root if there is none. An environment variable named `DATABASE_URL` overrides the file.
- Only `mysql://` is supported. The port defaults to 3306. Percent-encode special characters in the password (for example `@` as `%40`).
- Passwords are never printed; they appear as `***`.

To start the local MySQL 8.4 sandbox from the repository (Linux and macOS, or Git Bash or WSL on Windows):

```bash
./mysql/reset.sh
```

This deletes and recreates the sandbox's data volume. Use `./mysql/reset.sh --load` to start it with the data already loaded. On Windows without Git Bash or WSL, point `DATABASE_URL` at your own MySQL 8.x server instead.

## Usage

```bash
ie6700 load                    # create the course database (run once, on an empty server)
ie6700 queries                 # run queries.sql and print every result set
ie6700 test                    # run delete_rules.sql; exit status 1 if any rule fails
ie6700 status                  # server version and row count per table
ie6700 queries --format json   # also: --format csv (data on stdout, progress on stderr)
python -m ie6700 --help        # the same program, started as a module
```

Exit status: `0` success, `1` a database, SQL or verification failure, `2` a usage or configuration problem.

The SQL files under `mysql/` are read only. The commands never change them.

## Troubleshooting

- **`DATABASE_URL is not set`** (exit 2): copy `.env.example` to `.env`, or set the `DATABASE_URL` environment variable.
- **`DATABASE_URL is malformed` or `Only mysql:// is supported`** (exit 2): check the format above. Percent-encode special characters in the password.
- **`The server reports MariaDB` or `The server is MySQL 5.x`** (exit 1): the course schema needs MySQL 8.x. Use the sandbox from `./mysql/reset.sh`, or a MySQL 8.x server.
- **`Table 'Campus' already exists`** (exit 1): the database was loaded before. Reset it (`./mysql/reset.sh`, or `DROP DATABASE seattle_marketplace` on your own server), then run `ie6700 load` again.
- **`The database seattle_marketplace does not exist`** (exit 1): run `ie6700 load` first.
- **`SQL directory not found`** (exit 1): run `pip install -e .` from the repository so the package can find `mysql/`, or set `IE6700_SQL_DIR` to the folder that holds `marketplace.sql` and the other course files.
- **`Cannot connect` or `MySQL error at mysql://...`**: check that the server is running (for the sandbox, `docker ps` should list `neu-ie6700-mysql-mysql-1`) and that the host and port in `DATABASE_URL` match it.
- **PowerShell refuses to run `Activate.ps1`**: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

## Tests

```bash
python -m pytest tests            # unit tests; integration tests are skipped without DATABASE_URL
python -m pytest tests/integration  # expected results; needs a loaded server
```

The expected row counts and health-check names are in `tests/expected/`. A deliberate seed-data change should update them in the same commit.
