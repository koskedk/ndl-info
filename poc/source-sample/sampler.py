#!/usr/bin/env python3
"""Builds the stand-in S3 Ceph: copies the sampled facilities' rows from the real S3 Ceph.

It is a tool for building the stand-in, not part of NHAI. It reads three managed lists:
  ../transform/seeds/master_facility_list.csv   the facilities
  ../transform/seeds/facility_source_keys.csv   each system's key for a facility, and whether to copy it (in_sample)
  sample-tables.csv                             which tables, and how rows are chosen
  column-rules.csv                              which text columns arrive empty

    sampler.py measure          show how many source files each table needs; copies nothing
    sampler.py sample           copy the tables into the stand-in (replaces what is there)
    sampler.py verify           count the same rows on the real S3 Ceph and compare

Only totals are printed. Rows are never shown.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pyarrow.dataset as ds
from dotenv import dotenv_values
from pyarrow import fs as pafs
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.conversions import from_bytes
from pyiceberg.manifest import ManifestContent
from pyiceberg.table import StaticTable

HERE = Path(__file__).resolve().parent
POC = HERE.parent
REPO = POC.parent
FACILITIES = POC / "transform" / "seeds" / "master_facility_list.csv"
SOURCE_KEYS = POC / "transform" / "seeds" / "facility_source_keys.csv"
TABLES = HERE / "sample-tables.csv"
RULES = HERE / "column-rules.csv"
MANIFESTS = HERE / "manifests"
WORK = POC / ".data" / "sampler"

# The source's history is replayed as three loads, split on each row's own change date,
# so that "pick up only what is new" can be tested against the stand-in.
LOAD_CUTOFFS = ["2026-07-01", "2026-10-01"]
MANIFEST_WORKERS = 24

# Settings: the real S3 Ceph from the repository's .env, the stand-in from poc/.env.
for key, value in dotenv_values(REPO / ".env").items():
    if value is not None:
        os.environ.setdefault(key, value)
STANDIN = dotenv_values(POC / ".env")

from lake_explorer import iceberg as lake_iceberg, store as lake_store  # noqa: E402
from lake_explorer.config import load_config  # noqa: E402
from lake_explorer.engine import Engine  # noqa: E402


def say(message: str) -> None:
    print(message, flush=True)


def quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def in_list(values) -> str:
    return "(" + ", ".join(quote(v) for v in values) + ")"


# -- the three lists -------------------------------------------------------------

def sampled_facilities() -> dict[str, dict]:
    """Per source system: the facility keys to copy, and for Tiberbu the counties they are in."""
    county = {row["fid"]: row["county"] for row in csv.DictReader(FACILITIES.open())}
    out: dict[str, dict] = {}
    for row in csv.DictReader(SOURCE_KEYS.open()):
        if row["in_sample"].strip().lower() != "true":
            continue
        if row["fid"] not in county:
            sys.exit(f"facility_source_keys.csv names {row['fid']}, which is not in master_facility_list.csv")
        entry = out.setdefault(row["source_system"], {"keys": [], "counties": set()})
        entry["keys"].append(row["source_facility_key"])
        if county[row["fid"]].strip():
            entry["counties"].add(re.sub(r"[^a-z0-9]+", "_", county[row["fid"]].strip().lower()).strip("_"))
    return out


def table_list() -> list[dict]:
    return list(csv.DictReader(TABLES.open()))


def emptied_columns(source: str, table: str) -> set[str]:
    return {r["column"] for r in csv.DictReader(RULES.open())
            if r["source"] == source and r["table"] == table and r["rule"] == "empty"}


# -- how rows are chosen ---------------------------------------------------------

FACILITY_COLUMN = {"tiberbu": "company", "kenyaemr": "source_schema", "amrs": "location_id"}
PRUNE_COLUMN = {"tiberbu": "county_id", "kenyaemr": "source_schema", "amrs": "location_id"}


def patient_link(source: str, table: str) -> tuple[list[str], list[str]]:
    """For a table chosen through another table's patients: the columns that name the patient
    in the parent table, and the matching columns in this one."""
    if source == "tiberbu":
        return ["county_id", "patient"], ["county_id", "name"]
    if source == "amrs":  # one database, so the patient number alone is enough
        return ["patient_id"], ["person_id" if table == "person" else "patient_id"]
    raise SystemExit(f"{source}.{table}: choosing rows through patients is not supported for {source} yet")


def selection(spec: dict, facilities: dict) -> tuple[str | None, list, str, str | None]:
    """For one table: the column files are skipped on, its values, the WHERE clause, the facility column."""
    source, how = spec["source"], spec["select_by"]
    chosen = facilities.get(source, {"keys": [], "counties": set()})
    if how == "whole":
        return None, [], "TRUE", None
    if source == "tiberbu":
        counties = sorted(chosen["counties"])
        if how == "facility":
            where = f"company IN {in_list(chosen['keys'])} AND county_id IN {in_list(counties)}"
            return "county_id", counties, where, "company"
        if how.startswith("patients_in:"):
            parent = f"tiberbu__{how.split(':', 1)[1]}"
            where = (f"county_id IN {in_list(counties)} AND (county_id, name) IN "
                     f'(SELECT DISTINCT county_id, patient FROM "{parent}")')
            return "county_id", counties, where, "county_id"
    if source == "kenyaemr" and how == "facility":
        return "source_schema", chosen["keys"], f"source_schema IN {in_list(chosen['keys'])}", "source_schema"
    if source == "amrs":
        if how == "facility":
            locations = sorted(int(key) for key in chosen["keys"])  # location_id is a number
            return "location_id", locations, f"location_id IN ({', '.join(map(str, locations))})", "location_id"
        if how.startswith("patients_in:"):
            # No column to skip files on: patients of the sampled locations are spread through the whole table.
            parent = f"amrs__{how.split(':', 1)[1]}"
            parent_columns, own_columns = patient_link(source, spec["table"])
            where = f'"{own_columns[0]}" IN (SELECT DISTINCT "{parent_columns[0]}" FROM "{parent}")'
            return None, [], where, None
    raise SystemExit(f"{source}.{spec['table']}: select_by '{how}' is not supported yet")


# -- reading the real S3 Ceph ----------------------------------------------------

def plan_files(table: StaticTable, column: str | None, values: list) -> dict:
    """The source data files worth reading, using each file's recorded lowest and highest value."""
    snapshot = table.current_snapshot()
    if snapshot is None:
        return {"keep": [], "files": 0, "bytes": 0, "keep_bytes": 0, "rows": 0}
    io = table.io
    manifests = lake_store.retrying(lambda: snapshot.manifests(io))
    field = table.schema().find_field(column) if column else None
    done = 0

    def read(manifest):
        entries = lake_store.retrying(lambda: list(manifest.fetch_manifest_entry(io, discard_deleted=True)))
        out = []
        for entry in entries:
            f = entry.data_file
            keep = True
            if field is not None:
                low = (f.lower_bounds or {}).get(field.field_id)
                high = (f.upper_bounds or {}).get(field.field_id)
                if low is not None and high is not None:
                    lo, hi = from_bytes(field.field_type, low), from_bytes(field.field_type, high)
                    keep = any(lo <= v <= hi for v in values)
            out.append((f.file_path, f.record_count, f.file_size_in_bytes, keep))
        return manifest.content == ManifestContent.DATA, out

    keep, files, size, keep_size, rows = [], 0, 0, 0, 0
    with ThreadPoolExecutor(max_workers=MANIFEST_WORKERS) as pool:
        for is_data, entries in pool.map(read, manifests):
            done += 1
            if done % max(1, len(manifests) // 5) == 0 or done == len(manifests):
                say(f"      reading load records: {done:,} of {len(manifests):,}")
            if not is_data:
                if entries:
                    raise SystemExit("this table has row-level deletes, which the sampler does not handle yet")
                continue
            for path, count, nbytes, wanted in entries:
                files += 1
                size += nbytes
                rows += count
                if wanted:
                    keep.append(path.removeprefix("s3://").removeprefix("s3a://"))
                    keep_size += nbytes
    return {"keep": keep, "files": files, "bytes": size, "keep_bytes": keep_size, "rows": rows}


def read_source(con, sql: str, attempts: int = 6) -> None:
    """Run a query that reads the real S3 Ceph, starting it again if the connection drops.

    DuckDB reports a dropped connection as its own kind of error, which the explorer's
    retry does not recognise, so it is caught here.
    """
    for attempt in range(1, attempts + 1):
        try:
            con.execute(sql).fetchall()
            return
        except (duckdb.Error, OSError) as exc:
            dropped = any(word in str(exc) for word in ("NETWORK_CONNECTION", "Timeout", "timed out", "curlCode", "SLOW_DOWN", "503", "Connection reset", "Temporary failure"))
            if not dropped or attempt == attempts:
                raise
            pause = min(30 * attempt, 120)
            say(f"      connection dropped (attempt {attempt} of {attempts}); starting this table again in {pause}s")
            time.sleep(pause)


def mb(n: int) -> str:
    return f"{n / 1024 / 1024:,.0f} MB"


# -- writing the stand-in --------------------------------------------------------

def standin_properties() -> dict[str, str]:
    return {
        "s3.endpoint": STANDIN["STANDIN_S3_ENDPOINT"],
        "s3.access-key-id": STANDIN["STANDIN_S3_WRITE_ACCESS_KEY"],
        "s3.secret-access-key": STANDIN["STANDIN_S3_WRITE_SECRET_KEY"],
        "s3.region": STANDIN.get("STANDIN_S3_REGION", "us-east-1"),
        "s3.force-virtual-addressing": "false",
        "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
    }


def standin_filesystem() -> pafs.S3FileSystem:
    endpoint = STANDIN["STANDIN_S3_ENDPOINT"]
    return pafs.S3FileSystem(
        access_key=STANDIN["STANDIN_S3_WRITE_ACCESS_KEY"], secret_key=STANDIN["STANDIN_S3_WRITE_SECRET_KEY"],
        endpoint_override=re.sub(r"^https?://", "", endpoint), scheme="https" if endpoint.startswith("https") else "http",
        region=STANDIN.get("STANDIN_S3_REGION", "us-east-1"), force_virtual_addressing=False, allow_bucket_creation=True,
    )


def load_number(column: str) -> str:
    """SQL giving 1, 2 or 3: which replayed load a row belongs to."""
    if not column:
        return "1"
    parts = [f'WHEN "{column}" IS NULL OR "{column}" < TIMESTAMP {quote(LOAD_CUTOFFS[0])} THEN 1']
    for n, cutoff in enumerate(LOAD_CUTOFFS[1:], start=2):
        parts.append(f'WHEN "{column}" < TIMESTAMP {quote(cutoff)} THEN {n}')
    return "CASE " + " ".join(parts) + f" ELSE {len(LOAD_CUTOFFS) + 1} END"


def facility_month_counts(con, local: str, facility: str | None, date_column: str) -> list[dict]:
    if not facility or not date_column:
        return []
    rows = con.execute(
        f'SELECT CAST("{facility}" AS VARCHAR), strftime(date_trunc(\'month\', "{date_column}"), \'%Y-%m\'), count(*) '
        f'FROM "{local}" GROUP BY ALL ORDER BY 1, 2').fetchall()
    return [{"facility": f, "month": m, "rows": n} for f, m, n in rows]


# -- commands --------------------------------------------------------------------

def open_sources():
    config = load_config()
    return config, {name: config.source(name) for name in {t["source"] for t in table_list()}}


def run(args) -> int:
    facilities = sampled_facilities()
    config, sources = open_sources()
    measure_only = args.command == "measure"

    con = bucket = catalog = fs = None
    if not measure_only:
        shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True, exist_ok=True)
        MANIFESTS.mkdir(exist_ok=True)
        con = duckdb.connect(str(WORK / "work.duckdb"))
        con.execute("SET memory_limit='3GB'")
        con.execute(f"SET temp_directory='{WORK / 'tmp'}'")
        con.execute("SET preserve_insertion_order=false")
        bucket = STANDIN["STANDIN_S3_BUCKETS"].split(",")[0]
        fs = standin_filesystem()
        fs.create_dir(bucket)
        catalog = SqlCatalog("standin", uri="sqlite:///:memory:", warehouse=f"s3://{bucket}", **standin_properties())
        catalog.create_namespace("standin")

    total = table_list()
    if args.only:
        wanted = set(args.only.split(","))
        total = [t for t in total if f"{t['source']}.{t['table']}" in wanted]
        if not total:
            sys.exit(f"--only names no table in sample-tables.csv: {args.only}")
    for number, spec in enumerate(total, start=1):
        source, name = spec["source"], spec["table"]
        label = f"{source}.{name}"
        say(f"\n[{number}/{len(total)}] {label}")
        started = time.time()
        src = sources[source]
        table = lake_iceberg.open_table(src, name)
        column, values, where, facility_column = selection(spec, facilities)
        plan = plan_files(table, column, values)
        share = 100 * plan["keep_bytes"] / plan["bytes"] if plan["bytes"] else 0
        say(f"      source: {plan['rows']:,} rows in {plan['files']:,} files ({mb(plan['bytes'])})")
        say(f"      to read: {len(plan['keep']):,} files ({mb(plan['keep_bytes'])}, {share:.0f}% of the table)")
        if measure_only:
            continue

        local = f"{source}__{name}"
        arrow_schema = table.schema().as_arrow()
        if plan["keep"]:
            dataset = ds.dataset(plan["keep"], filesystem=lake_store.filesystem(src.store), format="parquet", schema=arrow_schema)
        else:
            dataset = arrow_schema.empty_table()
        con.register("source_rows", dataset)
        empty = emptied_columns(source, name)
        columns = ", ".join(f'CAST(NULL AS VARCHAR) AS "{f.name}"' if f.name in empty else f'"{f.name}"' for f in arrow_schema)
        read_source(con, f'CREATE OR REPLACE TABLE "{local}" AS SELECT {columns} FROM source_rows WHERE {where}')
        con.unregister("source_rows")
        kept = con.execute(f'SELECT count(*) FROM "{local}"').fetchall()[0][0]
        say(f"      kept: {kept:,} rows ({time.time() - started:.0f}s)")

        # For a table chosen through another table's patients: how many of those patients the source holds.
        referred = found = None
        if spec["select_by"].startswith("patients_in:"):
            parent = f"{source}__{spec['select_by'].split(':', 1)[1]}"
            theirs, ours = patient_link(source, name)
            their_list, our_list = (", ".join(f'"{c}"' for c in cols) for cols in (theirs, ours))
            match = " AND ".join(f'p."{o}" = e."{t}"' for t, o in zip(theirs, ours))
            referred, found = con.execute(
                f'SELECT count(*), count(p."{ours[-1]}") FROM (SELECT DISTINCT {their_list} FROM "{parent}") e '
                f'LEFT JOIN (SELECT DISTINCT {our_list} FROM "{local}") p ON {match}').fetchall()[0]
            say(f"      patients the sampled {parent.split('__')[1]} rows refer to: {referred:,}; "
                f"in the source and copied: {found:,}; not in the source: {referred - found:,}")

        # Write the stand-in table: same folder, same columns, no catalog, three loads.
        location = f"{bucket}/{src.path}/{name}"
        fs.delete_dir_contents(location, missing_dir_ok=True)
        target = catalog.create_table(f"standin.{local}", schema=table.schema(), location=f"s3://{location}")
        by_load = {}
        load_sql = load_number(spec["load_date_column"])
        for load in range(1, len(LOAD_CUTOFFS) + 2):
            rows = con.sql(f'SELECT * FROM "{local}" WHERE {load_sql} = {load}').to_arrow_table()
            if rows.num_rows == 0:
                continue
            target.append(rows.cast(target.schema().as_arrow()),
                          snapshot_properties={"sampler.load": str(load), "sampler.source-snapshot": str(table.current_snapshot().snapshot_id)})
            by_load[str(load)] = rows.num_rows
        say(f"      written to the stand-in in {len(by_load)} load(s): {', '.join(f'{n:,}' for n in by_load.values()) or 'no rows'}")

        # Read the stand-in back and check it.
        target.refresh()
        back = target.scan().to_arrow()
        con.register("standin_rows", back)
        filled = [c for c in sorted(empty)
                  if con.execute(f'SELECT count("{c}") FROM standin_rows').fetchall()[0][0] > 0] if back.num_rows else []
        con.unregister("standin_rows")
        problems = []
        if back.num_rows != kept:
            problems.append(f"the stand-in holds {back.num_rows:,} rows but {kept:,} were kept")
        if filled:
            problems.append(f"columns that should be empty are not: {', '.join(filled)}")
        say("      check: " + ("; ".join(problems) if problems else f"stand-in holds {back.num_rows:,} rows; {len(empty)} emptied columns are empty"))

        by_facility = {}
        if facility_column:
            by_facility = {str(k): n for k, n in con.execute(
                f'SELECT "{facility_column}", count(*) FROM "{local}" GROUP BY ALL ORDER BY 1').fetchall()}
        manifest = {
            "source": source, "table": name,
            "sampled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_metadata_file": table.metadata_location.rsplit("/", 1)[-1],
            "source_snapshot_id": table.current_snapshot().snapshot_id,
            "select_by": spec["select_by"],
            "source_rows": plan["rows"], "source_files": plan["files"], "source_bytes": plan["bytes"],
            "files_read": len(plan["keep"]), "bytes_read": plan["keep_bytes"],
            "rows_kept": kept, "rows_by_facility": by_facility, "rows_by_load": by_load,
            "patients_referred_to": referred, "patients_in_source": found,
            "rows_by_facility_month": facility_month_counts(con, local, facility_column if spec["select_by"] == "facility" else None, spec["load_date_column"]),
            "emptied_columns": sorted(empty),
            "standin_location": f"s3://{location}",
            "problems": problems,
        }
        (MANIFESTS / f"{source}.{name}.json").write_text(json.dumps(manifest, indent=2) + "\n")
        if problems:
            con.close()
            return 1

    if con is not None:
        con.close()
        shutil.rmtree(WORK, ignore_errors=True)  # the working copy held rows; remove it
        say("\nDone. Working files removed. Totals are in source-sample/manifests/.")
    return 0


def verify(args) -> int:
    """Counts the same rows on the real S3 Ceph, reading every file, and compares with what was kept."""
    facilities = sampled_facilities()
    config, _ = open_sources()
    engine = Engine(config, memory_limit="3GB", log=lambda m: say(f"      {m}"))
    failed = 0
    only = set(args.only.split(",")) if args.only else None
    for spec in table_list():
        if spec["select_by"] != "facility":
            continue
        if only and f"{spec['source']}.{spec['table']}" not in only:
            continue
        source, name = spec["source"], spec["table"]
        manifest_file = MANIFESTS / f"{source}.{name}.json"
        if not manifest_file.exists():
            say(f"\n{source}.{name}: not sampled yet")
            failed += 1
            continue
        manifest = json.loads(manifest_file.read_text())
        _, _, where, facility_column = selection(spec, facilities)
        date_column = spec["load_date_column"]
        say(f"\n{source}.{name}: counting on the real S3 Ceph")
        _, rows = engine.run(
            f'SELECT CAST("{facility_column}" AS VARCHAR), strftime(date_trunc(\'month\', "{date_column}"), \'%Y-%m\'), count(*) '
            f"FROM {source}.{name} WHERE {where} GROUP BY ALL")
        there = {(f, m): n for f, m, n in rows}
        here = {(r["facility"], r["month"]): r["rows"] for r in manifest["rows_by_facility_month"]}
        differences = [key for key in set(there) | set(here) if there.get(key, 0) != here.get(key, 0)]
        newer = sum(there.values()) - sum(here.values())
        if differences:
            failed += 1
            say(f"      DIFFERENT in {len(differences)} facility-months; source has {newer:+,} rows compared with the sample")
        else:
            say(f"      same: {sum(here.values()):,} rows across {len(here)} facility-months")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["measure", "sample", "verify"])
    parser.add_argument("--only", help="comma-separated source.table names; a table chosen by patients_in needs its parent in the same run")
    args = parser.parse_args()
    if not sampled_facilities():
        sys.exit("No row in facility_source_keys.csv has in_sample = true.")
    return verify(args) if args.command == "verify" else run(args)


if __name__ == "__main__":
    sys.exit(main())
