#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  printf 'Usage: %s [--load] [--help]\n' "$0"
  printf 'Recreate the neu-ie6700-mysql sandbox (MySQL 8.4) with an empty data volume.\n'
  printf 'All database data in this sandbox is deleted; archive/ is preserved.\n'
  printf '  --load  also import marketplace.sql and seed/ inside the container (same as ./db.sh load).\n'
  printf 'Without --load the sandbox is empty; the original SQL files are never imported.\n'
}

load=0
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi
if [[ $# -eq 1 ]]; then
  case "$1" in
    --help) usage; exit 0 ;;
    --load) load=1 ;;
    *) usage >&2; exit 2 ;;
  esac
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
compose=(docker compose
  --project-name neu-ie6700-mysql
  --project-directory "$script_dir"
  --file "$script_dir/docker-compose.yaml")

docker info >/dev/null
"${compose[@]}" config --quiet
"${compose[@]}" pull --policy missing mysql

on_error() {
  local status=$?
  printf 'Reset failed. Recent MySQL logs follow:\n' >&2
  "${compose[@]}" logs --no-color --tail 60 mysql >&2 || true
  exit "$status"
}
trap on_error ERR

printf 'Resetting the neu-ie6700-mysql sandbox and its database volume...\n'
"${compose[@]}" down --volumes
"${compose[@]}" up --detach --wait --wait-timeout 180 mysql
if [[ $load -eq 1 ]]; then
  "$script_dir/db.sh" load
  printf 'MySQL is ready with the schema and seed data loaded.\n'
else
  printf 'MySQL is ready. The sandbox is empty; run ./db.sh load to import the data.\n'
fi
