#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
Usage: ./db.sh <command>

  load      Import marketplace.sql and seed/*.sql into an empty sandbox (run ./reset.sh first
            if the database already exists).
  shell     Open the mysql client on the seattle_marketplace database.
  queries   Run queries.sql (reads data; every change in it is rolled back).
  test      Run delete_rules.sql (delete-rule tests, prints PASS or FAIL for each rule).
  status    Show the server version, the tables and their row counts.

Start or recreate the container with ./reset.sh (add --load to import the data as well).
USAGE
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
compose=(docker compose
  --project-name neu-ie6700-mysql
  --project-directory "$script_dir"
  --file "$script_dir/docker-compose.yaml")

require_running() {
  if [[ -z "$("${compose[@]}" ps --status running --quiet mysql)" ]]; then
    printf 'The MySQL container is not running. Start it with ./reset.sh\n' >&2
    exit 1
  fi
}

run_file() {
  local file="$1"; shift
  "${compose[@]}" exec -T mysql sh -c \
    'f="$1"; shift; MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --user=root "$@" < "$f"' sh "$file" "$@"
}

run_sql() {
  "${compose[@]}" exec -T mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --user=root "$@"' sh "$@"
}

case "${1:-}" in
  load)
    require_running
    for f in marketplace.sql seed/01_identity.sql seed/02_marketplace.sql seed/03_messaging_reviews_reports.sql; do
      printf 'Loading %s ... ' "$f"
      run_file "/workspace/$f"
      printf 'ok\n'
    done
    ;;
  shell)
    require_running
    exec "${compose[@]}" exec mysql sh -c \
      'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root seattle_marketplace'
    ;;
  queries)
    require_running
    run_file /workspace/queries.sql --table
    ;;
  test)
    require_running
    run_file /workspace/delete_rules.sql --table
    ;;
  status)
    require_running
    run_sql --table --execute="SELECT VERSION() AS mysql_version, @@character_set_server AS charset, @@collation_server AS collation, @@global.time_zone AS time_zone"
    run_sql --table seattle_marketplace --execute="SELECT table_name AS \`table\`, table_rows AS approx_rows FROM information_schema.tables WHERE table_schema = 'seattle_marketplace' ORDER BY table_name"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
