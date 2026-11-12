"""Run an additive count over a big lake table in batches of files, surviving VPN drops.

A plain `lake-explorer sql` query over a table of thousands of small files takes
many minutes, and one dropped connection loses the lot. This runs the same count
over a few hundred files at a time and saves each batch's totals, so a drop only
costs the batch in flight. Run it again and it carries on where it stopped.

Only use it for counts that can be added up across batches (count(*), sums). It is
not right for count(DISTINCT ...), which would count a value once per batch.

    uv run --offline python scripts/batched_count.py tiberbu form_data_repository \
        queries/batched/tiberbu_form_fields.sql out/tiberbu_form_fields

The SQL file must read from a table called `batch`. Batch results are written to
<out>.parts/ and nothing else is stored: no rows of the table are kept on disk.
"""

from __future__ import annotations

import csv
import json
import socket
import sys
import time
from pathlib import Path

import duckdb
import pyarrow.dataset as ds

from lake_explorer import iceberg, store as st
from lake_explorer.config import CACHE_DIR, load_config

BATCH_FILES = 250
WAIT_FOR_VPN_HOURS = 8
ATTEMPTS_PER_BATCH = 30


def reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=8):
            return True
    except OSError:
        return False


def wait_for_lake(host: str, port: int) -> None:
    deadline = time.time() + WAIT_FOR_VPN_HOURS * 3600
    told = False
    while not reachable(host, port):
        if not told:
            print("lake not reachable, waiting for the VPN ...", flush=True)
            told = True
        if time.time() > deadline:
            sys.exit(f"gave up after {WAIT_FOR_VPN_HOURS} hours without a connection")
        time.sleep(30)
    if told:
        print("lake reachable again", flush=True)


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    source_name, table, sql_path, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    sql = sql_path.read_text()
    cfg = load_config()
    source = cfg.source(source_name)
    host, _, port = source.store.host.partition(":")
    port = int(port) if port else (443 if source.store.scheme == "https" else 80)

    parts = Path(f"{out}.parts")
    parts.mkdir(parents=True, exist_ok=True)

    # The list of files is fixed on the first run, so later runs resume against the same batches.
    plan_file = parts / "files.json"
    wait_for_lake(host, port)
    tbl = st.retrying(lambda: iceberg.open_table(source, table))
    schema = tbl.schema().as_arrow()
    if plan_file.is_file():
        files = json.loads(plan_file.read_text())
    else:
        plan = iceberg.current_files(source, table, tbl)
        if plan.delete_files:
            sys.exit("table has delete files; use lake-explorer sql instead")
        files = list(plan.files)
        plan_file.write_text(json.dumps(files))
    batches = [files[i:i + BATCH_FILES] for i in range(0, len(files), BATCH_FILES)]
    print(f"{source_name}.{table}: {len(files):,} files in {len(batches)} batches", flush=True)

    fs = st.filesystem(source.store)
    spill = CACHE_DIR / "duckdb_tmp"
    spill.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for number, batch in enumerate(batches):
        part = parts / f"{number:04d}.csv"
        if part.is_file():
            continue
        for attempt in range(1, ATTEMPTS_PER_BATCH + 1):
            wait_for_lake(host, port)
            con = duckdb.connect()
            con.execute("SET memory_limit='4GB'")
            con.execute(f"SET temp_directory='{spill}'")
            con.execute("SET max_temp_directory_size='20GB'")
            try:
                con.register("batch", ds.dataset(batch, filesystem=fs, format="parquet", schema=schema))
                result = con.execute(sql)
                columns = [d[0] for d in result.description]
                rows = result.fetchall()
                break
            except Exception as exc:  # network errors surface as several different types
                print(f"batch {number + 1}: attempt {attempt} failed ({str(exc)[:120]})", flush=True)
                if attempt == ATTEMPTS_PER_BATCH:
                    raise
                time.sleep(20)
            finally:
                con.close()
        tmp = part.with_suffix(".tmp")
        with tmp.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)
        tmp.rename(part)
        print(f"batch {number + 1} of {len(batches)} done", flush=True)
    print("all batches done", flush=True)


if __name__ == "__main__":
    main()
