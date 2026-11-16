#!/usr/bin/env bash
# Clears every copy of the POC's data from this machine.
# See "Clearing all data on demand" in PLAN.md. Run it through `make purge`.
#
#   DRY_RUN=1       list what would be removed and stop
#   CONFIRM=purge   skip the typed confirmation (for a scripted run)
#
# Exit codes: 0 done, 1 not confirmed, 2 cannot run safely, 3 something was left behind.
set -euo pipefail

POC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(dirname "$POC_DIR")"
# The Compose project name: `nhai-poc` unless COMPOSE_PROJECT_NAME is set in .env.
PROJECT="${NHAI_COMPOSE_PROJECT:-$(cd "$POC_DIR" && docker compose config --format json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])' 2>/dev/null || true)}"
PROJECT="${PROJECT:-nhai-poc}"
DRY_RUN="${DRY_RUN:-0}"
LOG="$POC_DIR/purge.log"

# Folders and files that can hold data.
TARGETS=(
  "$POC_DIR/.data"               # Trino spill, Dagster local storage, anything bind-mounted
  "$POC_DIR/exports"             # encrypted exports of the stand-in
  "$POC_DIR/matching/data"       # Splink inputs and outputs
  "$POC_DIR/transform/target"    # compiled SQL, which carries the hash key
  "$POC_DIR/transform/logs"
  "$POC_DIR/.secrets/hash_key"   # the hash key itself
)
# Where the lake explorer sits beside this folder, its query results and caches go too.
EXPLORER_DIR=""
if [[ -d "$REPO_DIR/explorer/src/lake_explorer" ]]; then
  EXPLORER_DIR="$REPO_DIR/explorer"
  TARGETS+=("$EXPLORER_DIR/out" "$EXPLORER_DIR/.cache")
fi

fail() { echo "purge: $*" >&2; exit 2; }

[[ -f "$POC_DIR/PLAN.md" && -f "$POC_DIR/compose.yaml" ]] || fail "this does not look like the project folder ($POC_DIR); nothing removed"

docker_up=1
docker info >/dev/null 2>&1 || docker_up=0
if [[ $docker_up -eq 0 && $DRY_RUN != 1 ]]; then
  fail "Docker is not running, so its volumes cannot be removed or checked. Start Docker Desktop and run again."
fi

list_containers() { docker ps -aq --filter "label=com.docker.compose.project=$PROJECT"; }
list_volumes()    { docker volume ls -q --filter "label=com.docker.compose.project=$PROJECT"; }
list_paths() {
  local target
  for target in "${TARGETS[@]}"; do
    [[ -e "$target" ]] && echo "$target"
  done
  # DuckDB files left anywhere under the folders that run queries.
  find ${EXPLORER_DIR:+"$EXPLORER_DIR"} "$POC_DIR" \( -name '*.duckdb' -o -name '*.duckdb.wal' \) \
    -not -path '*/.venv/*' -not -path '*/node_modules/*' 2>/dev/null || true
}

containers=(); volumes=()
if [[ $docker_up -eq 1 ]]; then
  mapfile -t containers < <(list_containers)
  mapfile -t volumes < <(list_volumes)
fi
mapfile -t paths < <(list_paths | sort -u)

echo "Project: $PROJECT"
echo "Containers to remove: ${#containers[@]}"
echo "Volumes to remove:    ${#volumes[@]}"
for v in "${volumes[@]}"; do echo "  $v"; done
echo "Folders and files to remove: ${#paths[@]}"
for p in "${paths[@]}"; do echo "  ${p#"$POC_DIR"/}  ($(du -sh "$p" 2>/dev/null | cut -f1))"; done
[[ $docker_up -eq 0 ]] && echo "Docker is not running: volumes were not listed."

if [[ $DRY_RUN == 1 ]]; then
  echo "Dry run: nothing removed."
  exit 0
fi

if [[ "${CONFIRM:-}" != "purge" ]]; then
  read -r -p "Type purge to delete all of the above: " answer || answer=""
  [[ "$answer" == "purge" ]] || { echo "Not confirmed. Nothing removed."; exit 1; }
fi

if [[ ${#containers[@]} -gt 0 ]]; then docker rm -f "${containers[@]}" >/dev/null; fi
if [[ ${#volumes[@]} -gt 0 ]]; then docker volume rm "${volumes[@]}" >/dev/null; fi
for p in "${paths[@]}"; do
  real="$(realpath -m "$p")"
  [[ "$real" == "$POC_DIR"/* || ( -n "$EXPLORER_DIR" && "$real" == "$EXPLORER_DIR"/* ) ]] || fail "$p points outside the project; stopped before removing it"
  rm -rf -- "$real"
done

# Check that nothing is left.
left=()
mapfile -t still_containers < <(list_containers)
mapfile -t still_volumes < <(list_volumes)
mapfile -t still_paths < <(list_paths | sort -u)
left+=("${still_containers[@]}" "${still_volumes[@]}" "${still_paths[@]}")

stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
summary="project=$PROJECT containers=${#containers[@]} volumes=${#volumes[@]} paths=${#paths[@]}"
if [[ ${#left[@]} -gt 0 ]]; then
  echo "$stamp purge INCOMPLETE $summary left=${#left[@]}" >> "$LOG"
  echo "Still present:" >&2
  for item in "${left[@]}"; do echo "  $item" >&2; done
  exit 3
fi
echo "$stamp purge complete $summary" >> "$LOG"
echo "Done. Nothing is left. Recorded in ${LOG#"$POC_DIR"/}."
echo "Exports already sent to someone else, and notebooks the row browser keeps in ~/.duckdb, are not covered."
