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
PROJECT="${NHAI_COMPOSE_PROJECT:-nhai-poc}"
DRY_RUN="${DRY_RUN:-0}"
LOG="$POC_DIR/purge.log"

# Folders and files that can hold data, relative to the repository.
TARGETS=(
  "explorer/out"            # query results
  "explorer/.cache"         # file lists and DuckDB spill
  "poc/.data"               # Trino spill, Dagster local storage, anything bind-mounted
  "poc/matching/data"       # Splink inputs and outputs
  "poc/transform/target"    # compiled SQL, which carries the hash key
  "poc/transform/logs"
  "poc/.secrets/hash_key"   # the hash key itself
)

fail() { echo "purge: $*" >&2; exit 2; }

[[ -d "$REPO_DIR/.git" && -f "$POC_DIR/PLAN.md" ]] || fail "this does not look like the project folder ($REPO_DIR); nothing removed"

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
    [[ -e "$REPO_DIR/$target" ]] && echo "$REPO_DIR/$target"
  done
  # DuckDB files left anywhere under the two folders that run queries.
  find "$REPO_DIR/explorer" "$POC_DIR" \( -name '*.duckdb' -o -name '*.duckdb.wal' \) \
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
for p in "${paths[@]}"; do echo "  ${p#"$REPO_DIR"/}  ($(du -sh "$p" 2>/dev/null | cut -f1))"; done
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
  [[ "$real" == "$REPO_DIR"/* ]] || fail "$p points outside the project; stopped before removing it"
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
echo "Done. Nothing is left. Recorded in ${LOG#"$REPO_DIR"/}."
