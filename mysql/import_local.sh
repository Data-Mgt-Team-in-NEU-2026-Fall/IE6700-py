#!/usr/bin/env bash
# One-shot import of the Seattle campus marketplace schema and sample data into a
# local MySQL 8.x server. Does not need Docker. Run it once per server; it stops
# if the database already exists unless --drop-existing is given.
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
Usage: ./import_local.sh [options]

Imports marketplace.sql and seed/*.sql into a local MySQL 8.x server, in order.
Needs the mysql client and a MySQL 8.x server. MariaDB is refused: the schema
uses the utf8mb4_0900_ai_ci collation, which only MySQL 8.x provides.

Options:
  -h, --host HOST       server host (default: 127.0.0.1)
  -P, --port PORT       server port (default: 3306)
  -u, --user USER       user with CREATE, DROP, INSERT and ALTER rights (default: root)
      --drop-existing   drop the seattle_marketplace database first if it exists
                        (deletes its data; without this flag the script stops instead)
      --help            show this help

Password: set MYSQL_PWD to pass it in; otherwise the script asks for it once.
USAGE
}

host="127.0.0.1"
port="3306"
user="root"
drop_existing=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--host)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      host="$2"; shift 2 ;;
    -P|--port)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      port="$2"; shift 2 ;;
    -u|--user)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      user="$2"; shift 2 ;;
    --drop-existing)
      drop_existing=1; shift ;;
    --help)
      usage; exit 0 ;;
    *)
      usage >&2; exit 2 ;;
  esac
done

if ! [[ "$port" =~ ^[0-9]+$ ]]; then
  printf 'Port must be a number: %s\n' "$port" >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
files=(
  marketplace.sql
  seed/01_identity.sql
  seed/02_marketplace.sql
  seed/03_messaging_reviews_reports.sql
)

for f in "${files[@]}"; do
  if [[ ! -f "$script_dir/$f" ]]; then
    printf 'Missing file: %s\n' "$script_dir/$f" >&2
    exit 1
  fi
done

if ! command -v mysql >/dev/null 2>&1; then
  printf 'The mysql client was not found. Install MySQL 8.x client tools first.\n' >&2
  exit 1
fi

if [[ -z "${MYSQL_PWD+x}" ]]; then
  read -rsp "Password for ${user}@${host}:${port}: " MYSQL_PWD
  printf '\n'
  export MYSQL_PWD
fi

client=(mysql --protocol=TCP --host="$host" --port="$port" --user="$user" --default-character-set=utf8mb4)

loading=0
on_error() {
  local status=$?
  # A failed $(...) fires the trap in the subshell too; report only in the main shell.
  if [[ "$BASHPID" != "$$" ]]; then
    exit "$status"
  fi
  if [[ $loading -eq 1 ]]; then
    printf '\nImport stopped with an error (exit %d). The database is partly loaded.\n' "$status" >&2
    printf 'Re-run with --drop-existing to start again from an empty database.\n' >&2
  else
    printf '\nStopped with an error (exit %d). Nothing was loaded.\n' "$status" >&2
  fi
  exit "$status"
}
trap on_error ERR

# 1. Check the server: must be MySQL 8.x, not MariaDB.
printf 'Connecting to %s:%s as %s ... ' "$host" "$port" "$user"
version="$("${client[@]}" --batch --skip-column-names --execute='SELECT VERSION()')"
printf '%s\n' "$version"
if [[ "$version" == *MariaDB* ]]; then
  printf 'The server is MariaDB (%s). This schema needs MySQL 8.x.\n' "$version" >&2
  exit 1
fi
if [[ "$version" != 8.* ]]; then
  printf 'The server is MySQL %s. This schema needs MySQL 8.x.\n' "$version" >&2
  exit 1
fi

# 2. Refuse to overwrite an existing database unless asked.
exists="$("${client[@]}" --batch --skip-column-names --execute="SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = 'seattle_marketplace'")"
if [[ "$exists" == "1" ]]; then
  if [[ $drop_existing -eq 1 ]]; then
    printf 'Dropping the existing seattle_marketplace database ... '
    "${client[@]}" --execute='DROP DATABASE seattle_marketplace'
    printf 'ok\n'
  else
    printf 'The seattle_marketplace database already exists. Nothing was changed.\n' >&2
    printf 'Run again with --drop-existing to replace it.\n' >&2
    exit 1
  fi
fi

# 3. Import the schema, then the sample data, in order.
loading=1
for f in "${files[@]}"; do
  printf 'Loading %s ... ' "$f"
  "${client[@]}" < "$script_dir/$f"
  printf 'ok\n'
done

# 4. Check the result: the schema has 23 base tables.
tables="$("${client[@]}" --batch --skip-column-names --execute="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'seattle_marketplace' AND table_type = 'BASE TABLE'")"
printf '\nLoaded seattle_marketplace with %s tables.\n' "$tables"
if [[ "$tables" != "23" ]]; then
  printf 'Expected 23 tables; check the output above.\n' >&2
  exit 1
fi
printf 'Done. Connect with: mysql -h %s -P %s -u %s seattle_marketplace\n' "$host" "$port" "$user"
