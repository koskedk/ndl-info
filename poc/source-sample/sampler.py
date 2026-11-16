#!/usr/bin/env python3
"""Builds the stand-in S3 Ceph: copies the sampled facilities' rows from the real S3 Ceph.

It is a tool for building the stand-in, not part of NHAI. It reads these managed lists:
  ../transform/seeds/master_facility_list.csv   the facilities
  ../transform/seeds/facility_source_keys.csv   each system's key for a facility, and whether to copy it (in_sample)
  sample-tables.csv                             which tables, and how rows are chosen
  visit-types.csv                               which visit types have their answers (obs) copied
  column-rules.csv                              which text columns arrive empty

How rows are chosen (select_by in sample-tables.csv):
  facility                  rows of the sampled facilities
  whole                     every row
  patients_in:a+b           rows of the patients that the sampled tables a and b refer to
  encounters_in:encounter   rows of the sampled encounters whose visit type is in visit-types.csv
  files                     plain files, copied as they are (KHIS)

A table chosen through another table reads that table's keys from the stand-in, so the other
table must have been sampled first (in this run or an earlier one).

    sampler.py measure          show how many source files each table needs; copies nothing
    sampler.py sample           copy the tables into the stand-in (replaces what is there)
    sampler.py verify           count the same rows on the real S3 Ceph and compare

Reading is done in groups of files. If a run stops part-way, running it again continues from
the last finished group. `--fresh` forgets that and starts each table again.

Only totals are printed. Rows are never shown.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
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
import pyarrow.parquet as pq
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
VISIT_TYPES = HERE / "visit-types.csv"
RULES = HERE / "column-rules.csv"
MANIFESTS = HERE / "manifests"
WORK = POC / ".data" / "sampler"

# The source's history is replayed as three loads, split on each row's own change date,
# so that "pick up only what is new" can be tested against the stand-in.
LOAD_CUTOFFS = ["2026-07-01", "2026-10-01"]
MANIFEST_WORKERS = 24

# Source files are read in groups. A group is finished, and recorded as finished, in one step,
# so a dropped connection costs one group and a rerun continues after the last finished one.
GROUP_FILES = 200
GROUP_BYTES = 300 * 1024 * 1024
DROPPED = ("NETWORK_CONNECTION", "Timeout", "timed out", "curlCode", "SLOW_DOWN", "503", "Connection reset", "Temporary failure")

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


def mb(n: int) -> str:
    return f"{n / 1024 / 1024:,.0f} MB"


def took(started: float) -> str:
    seconds = int(time.time() - started)
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


# -- the lists -------------------------------------------------------------------

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


def visit_types(source: str) -> dict[str, str]:
    """The visit types whose answers are copied for one system: lower-cased name -> name as listed."""
    return {row["encounter_type"].strip().lower(): row["encounter_type"].strip()
            for row in csv.DictReader(VISIT_TYPES.open()) if row["source"] == source}


def emptied_columns(source: str, table: str) -> set[str]:
    return {r["column"] for r in csv.DictReader(RULES.open())
            if r["source"] == source and r["table"] == table and r["rule"] == "empty"}


# -- the stand-in ----------------------------------------------------------------

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


def standin_bucket() -> str:
    return STANDIN["STANDIN_S3_BUCKETS"].split(",")[0]


def standin_table(src, name: str) -> StaticTable | None:
    """The stand-in's copy of a table, or None when it has not been sampled yet."""
    folder = f"{standin_bucket()}/{src.path}/{name}/metadata"
    found = standin_filesystem().get_file_info(pafs.FileSelector(folder, allow_not_found=True))
    versions = sorted(f.path for f in found if f.path.endswith(".metadata.json"))
    if not versions:
        return None
    return StaticTable.from_metadata(f"s3://{versions[-1]}", properties=standin_properties())


def keys_from_standin(con, src, source: str, table: str, columns: list[str]) -> str:
    """Loads a few columns of an already-sampled table from the stand-in into the work database."""
    copy = standin_table(src, table)
    if copy is None:
        raise SystemExit(f"{source}.{table} is not in the stand-in yet. Sample it first; other tables are chosen through it.")
    rows = copy.scan(selected_fields=tuple(columns)).to_arrow()
    name = f"{source}__{table}__keys"
    con.register("standin_keys", rows)
    con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM standin_keys')
    con.unregister("standin_keys")
    say(f"      {source}.{table}: {rows.num_rows:,} rows of keys read from the stand-in")
    return name


# -- how rows are chosen ---------------------------------------------------------

FACILITY_COLUMN = {"tiberbu": "company", "kenyaemr": "source_schema", "amrs": "location_id"}


def patient_link(source: str, table: str) -> tuple[list[str], list[str]]:
    """For a table chosen through other tables' patients: the columns that name the patient
    in those tables, and the matching columns in this one."""
    if source == "tiberbu":
        return ["county_id", "patient"], ["county_id", "name"]
    if source == "amrs":  # one database, so the patient number alone is enough
        return ["patient_id"], ["person_id" if table == "person" else "patient_id"]
    raise SystemExit(f"{source}.{table}: choosing rows through patients is not supported for {source} yet")


def choose(con, spec: dict, facilities: dict, sources: dict, rows_wanted: bool = True) -> dict:
    """How one table's rows are chosen.

    Returns the column source files are skipped on and its values (sorted), the WHERE clause,
    the facility column, and the names of the work tables holding patient keys or chosen
    encounters. With rows_wanted False only what file skipping needs is worked out.
    """
    source, name, how = spec["source"], spec["table"], spec["select_by"]
    chosen = facilities.get(source, {"keys": [], "counties": set()})
    sel = {"prune": None, "values": [], "where": "TRUE", "facility": None, "patient_keys": None, "encounters": None}
    kind, _, rest = how.partition(":")
    parents = rest.split("+") if rest else []
    counties = sorted(chosen["counties"])

    if how == "whole":
        return sel

    if how == "facility":
        column = (spec.get("facility_column") or "").strip() or FACILITY_COLUMN.get(source)
        if source == "tiberbu":
            sel.update(prune="county_id", values=counties, facility=column,
                       where=f'"{column}" IN {in_list(chosen["keys"])} AND county_id IN {in_list(counties)}')
            return sel
        if source == "kenyaemr":
            sel.update(prune=column, values=sorted(chosen["keys"]), facility=column,
                       where=f'"{column}" IN {in_list(chosen["keys"])}')
            return sel
        if source == "amrs":
            locations = sorted(int(key) for key in chosen["keys"])  # location_id is a number
            sel.update(prune=column, values=locations, facility=column,
                       where=f'"{column}" IN ({", ".join(map(str, locations))})')
            return sel

    if kind == "patients_in" and parents:
        theirs, ours = patient_link(source, name)
        if source == "tiberbu":
            sel.update(prune="county_id", values=counties, facility="county_id")
        if not rows_wanted:
            return sel
        columns = ", ".join(f'"{c}"' for c in theirs)
        parts = []
        for parent in parents:
            keys = keys_from_standin(con, sources[source], source, parent, theirs)
            parts.append(f'SELECT DISTINCT {columns} FROM "{keys}" WHERE "{theirs[-1]}" IS NOT NULL')
        sel["patient_keys"] = f"{source}__patient_keys"
        con.execute(f'CREATE OR REPLACE TABLE "{sel["patient_keys"]}" AS ' + " UNION ".join(parts))
        if source == "tiberbu":
            listed = f'(SELECT county_id, patient FROM "{sel["patient_keys"]}")'
            match = f"(county_id, name) IN {listed}"
            if name == "patient":  # also the babies whose mother is one of those patients
                match += f" OR (county_id, custom_parent) IN {listed}"
            sel["where"] = f"county_id IN {in_list(counties)} AND ({match})"
        else:
            # No column to skip files on: patients of the sampled locations are spread through the whole table.
            sel["where"] = f'"{ours[0]}" IN (SELECT "{theirs[0]}" FROM "{sel["patient_keys"]}")'
        return sel

    if kind == "encounters_in" and parents == ["encounter"] and source in ("kenyaemr", "amrs"):
        types = visit_types(source)
        if not types:
            raise SystemExit(f"visit-types.csv lists no visit types for {source}, so {source}.{name} would be empty")
        scope = ["source_schema"] if source == "kenyaemr" else []  # a KenyaEMR id is unique within one facility
        encounters = keys_from_standin(con, sources[source], source, "encounter", scope + ["encounter_id", "encounter_type", "location_id"])
        names = keys_from_standin(con, sources[source], source, "encounter_type", scope + ["encounter_type_id", "name"])
        scoped = "source_schema, " if scope else ""
        facility = "e.source_schema" if scope else "CAST(e.location_id AS VARCHAR)"
        sel["encounters"] = f"{source}__chosen_encounters"
        con.execute(
            f'CREATE OR REPLACE TABLE "{sel["encounters"]}" AS '
            f'SELECT DISTINCT {"e.source_schema, " if scope else ""}e.encounter_id, {facility} AS facility, t.name AS visit_type '
            f'FROM "{encounters}" e JOIN (SELECT DISTINCT {scoped}encounter_type_id, lower(trim(name)) AS name FROM "{names}") t '
            f'ON t.encounter_type_id = e.encounter_type{" AND t.source_schema = e.source_schema" if scope else ""} '
            f"WHERE t.name IN {in_list(sorted(types))}")
        total = con.execute(f'SELECT count(*) FROM (SELECT DISTINCT {scoped}encounter_id FROM "{sel["encounters"]}")').fetchall()[0][0]
        say(f"      encounters of the listed visit types at the sampled facilities: {total:,}")
        if source == "kenyaemr":
            sel.update(prune="source_schema", values=sorted(chosen["keys"]), facility="source_schema",
                       where=f'source_schema IN {in_list(chosen["keys"])} AND (source_schema, encounter_id) IN '
                             f'(SELECT source_schema, encounter_id FROM "{sel["encounters"]}")')
        else:
            ids = [row[0] for row in con.execute(f'SELECT DISTINCT encounter_id FROM "{sel["encounters"]}" ORDER BY 1').fetchall()]
            between = f"encounter_id BETWEEN {ids[0]} AND {ids[-1]} AND " if ids else "FALSE AND "
            sel.update(prune="encounter_id", values=ids,
                       where=f'{between}encounter_id IN (SELECT encounter_id FROM "{sel["encounters"]}")')
        return sel

    raise SystemExit(f"{source}.{name}: select_by '{how}' is not supported yet")


# -- reading the real S3 Ceph ----------------------------------------------------

def any_between(values: list, low, high) -> bool:
    """Whether any of the sorted values lies between low and high."""
    at = bisect.bisect_left(values, low)
    return at < len(values) and values[at] <= high


def plan_files(table: StaticTable, snapshot, column: str | None, values: list) -> dict:
    """The source data files worth reading, using each file's recorded lowest and highest value."""
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
                    keep = any_between(values, from_bytes(field.field_type, low), from_bytes(field.field_type, high))
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
                    keep.append((path.removeprefix("s3://").removeprefix("s3a://"), nbytes))
                    keep_size += nbytes
    return {"keep": sorted(keep), "files": files, "bytes": size, "keep_bytes": keep_size, "rows": rows}


def file_groups(files: list[tuple[str, int]]):
    group, size = [], 0
    for path, nbytes in files:
        group.append((path, nbytes))
        size += nbytes
        if len(group) >= GROUP_FILES or size >= GROUP_BYTES:
            yield group
            group, size = [], 0
    if group:
        yield group


def read_group(con, statements: list[str], attempts: int = 6) -> None:
    """Runs one group's statements as a single step, starting the group again if the connection drops.

    DuckDB reports a dropped connection as its own kind of error, which the explorer's
    retry does not recognise, so it is caught here.
    """
    for attempt in range(1, attempts + 1):
        try:
            con.execute("BEGIN")
            for statement in statements:
                con.execute(statement)
            con.execute("COMMIT")
            return
        except (duckdb.Error, OSError) as exc:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            if not any(word in str(exc) for word in DROPPED) or attempt == attempts:
                raise
            pause = min(30 * attempt, 120)
            say(f"      connection dropped (attempt {attempt} of {attempts}); reading this group again in {pause}s")
            time.sleep(pause)


def saved_progress(con, label: str) -> tuple[int, str] | None:
    """The source snapshot and recipe a part-finished copy of this table was started with."""
    con.execute("CREATE TABLE IF NOT EXISTS _progress (tbl VARCHAR, snapshot_id BIGINT, recipe VARCHAR, path VARCHAR)")
    found = con.execute("SELECT DISTINCT snapshot_id, recipe FROM _progress WHERE tbl = ?", [label]).fetchall()
    return found[0] if len(found) == 1 else None


def forget_progress(con, label: str, local: str) -> None:
    con.execute("DELETE FROM _progress WHERE tbl = ?", [label])
    con.execute(f'DROP TABLE IF EXISTS "{local}"')


def copy_rows(con, label: str, local: str, plan: dict, select: str, arrow_schema, filesystem, snapshot_id: int, recipe: str) -> None:
    """Reads the wanted source files in groups, adding the chosen rows to the work table."""
    done = {path for (path,) in con.execute("SELECT path FROM _progress WHERE tbl = ?", [label]).fetchall()}
    exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [local]).fetchall()[0][0]
    if not done or not exists:
        forget_progress(con, label, local)
        con.register("source_rows", arrow_schema.empty_table())
        con.execute(f'CREATE TABLE "{local}" AS {select} LIMIT 0')
        con.unregister("source_rows")
        done = set()
    else:
        say(f"      continuing an earlier run: {len(done):,} of {len(plan['keep']):,} files were already read")
    todo = [(path, nbytes) for path, nbytes in plan["keep"] if path not in done]
    files_done = len(plan["keep"]) - len(todo)
    bytes_done = plan["keep_bytes"] - sum(nbytes for _, nbytes in todo)
    started = time.time()
    for group in file_groups(todo):
        paths = [path for path, _ in group]
        con.register("source_rows", ds.dataset(paths, filesystem=filesystem, format="parquet", schema=arrow_schema))
        finished = ", ".join(f"({quote(label)}, {snapshot_id}, {quote(recipe)}, {quote(path)})" for path in paths)
        read_group(con, [f'INSERT INTO "{local}" {select}', f"INSERT INTO _progress VALUES {finished}"])
        con.unregister("source_rows")
        files_done += len(group)
        bytes_done += sum(nbytes for _, nbytes in group)
        kept = con.execute(f'SELECT count(*) FROM "{local}"').fetchall()[0][0]
        say(f"      read {files_done:,} of {len(plan['keep']):,} files, {mb(bytes_done)} of {mb(plan['keep_bytes'])}; "
            f"rows kept so far: {kept:,} ({took(started)})")


# -- writing the stand-in --------------------------------------------------------

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


def patient_totals(con, spec: dict, sel: dict, local: str) -> dict:
    """For a table chosen through other tables' patients: how many of those patients the source holds."""
    source, name = spec["source"], spec["table"]
    theirs, ours = patient_link(source, name)
    our_list = ", ".join(f'"{c}"' for c in ours)
    match = " AND ".join(f'p."{o}" = e."{t}"' for t, o in zip(theirs, ours))
    referred, found = con.execute(
        f'SELECT count(*), count(p."{ours[-1]}") FROM "{sel["patient_keys"]}" e '
        f'LEFT JOIN (SELECT DISTINCT {our_list} FROM "{local}") p ON {match}').fetchall()[0]
    parents = spec["select_by"].split(":", 1)[1].replace("+", ", ")
    say(f"      patients the sampled {parents} rows refer to: {referred:,}; "
        f"in the source and copied: {found:,}; not in the source: {referred - found:,}")
    out = {"patients_referred_to": referred, "patients_in_source": found}
    if source == "tiberbu" and name == "patient":
        babies = con.execute(
            f'SELECT count(*) FROM (SELECT DISTINCT {our_list} FROM "{local}") p '
            f'WHERE NOT EXISTS (SELECT 1 FROM "{sel["patient_keys"]}" e WHERE {match})').fetchall()[0][0]
        say(f"      babies added through their mother's record: {babies:,}")
        out["babies_through_mother"] = babies
    return out


def encounter_totals(con, spec: dict, sel: dict, local: str) -> dict:
    """For a table chosen through encounters: how many of the chosen encounters have rows, by facility and visit type."""
    source = spec["source"]
    listed = visit_types(source)
    chosen = sel["encounters"]
    key = "source_schema, encounter_id" if source == "kenyaemr" else "encounter_id"
    on = "r.encounter_id = c.encounter_id" + (" AND r.source_schema = c.source_schema" if source == "kenyaemr" else "")
    con.execute(f'CREATE OR REPLACE TEMP TABLE _with_rows AS SELECT {key}, count(*) AS n FROM "{local}" GROUP BY ALL')

    one = "(c.source_schema, c.encounter_id)" if source == "kenyaemr" else "c.encounter_id"

    def split(column: str) -> list[dict]:
        rows = con.execute(
            f"SELECT c.{column}, count(DISTINCT {one}), count(DISTINCT {one}) FILTER (WHERE r.encounter_id IS NOT NULL), "
            f'coalesce(sum(r.n), 0) FROM "{chosen}" c LEFT JOIN _with_rows r ON {on} GROUP BY ALL ORDER BY 1').fetchall()
        return [{column: value, "encounters": a, "encounters_with_rows": b, "rows": int(n)} for value, a, b, n in rows]

    by_type = split("visit_type")
    for row in by_type:
        row["visit_type"] = listed.get(row["visit_type"], row["visit_type"])
    by_facility = split("facility")
    total, with_rows = con.execute(
        f'SELECT (SELECT count(*) FROM (SELECT DISTINCT {key} FROM "{chosen}")), (SELECT count(*) FROM _with_rows)').fetchall()[0]
    missing = sorted(set(listed.values()) - {row["visit_type"] for row in by_type})
    say(f"      encounters chosen: {total:,}; with at least one row here: {with_rows:,}")
    if missing:
        say(f"      visit types in the list with no encounter at the sampled facilities: {', '.join(missing)}")
    return {"encounters_chosen": total, "encounters_with_rows": with_rows, "by_visit_type": by_type,
            "by_facility": by_facility, "visit_types_without_encounters": missing}


def copy_files(spec: dict, src, measure_only: bool) -> tuple[dict, list[str]]:
    """Plain files (KHIS): every file called <table>.parquet under the source's folder, copied as it is."""
    source, name = spec["source"], spec["table"]
    theirs = lake_store.filesystem(src.store)
    wanted = [(e.path, e.size) for e in lake_store.ls(src.store, src.root, recursive=True)
              if not e.is_dir and e.name == f"{name}.parquet"]
    total = sum(size for _, size in wanted)
    say(f"      source: {len(wanted):,} files ({mb(total)}), copied as they are")
    if measure_only:
        return {}, []
    ours = standin_filesystem()
    bucket = standin_bucket()
    started = time.time()
    rows = copied = skipped = 0
    problems = []
    for number, (path, size) in enumerate(wanted, start=1):
        target = f"{bucket}/{path.split('/', 1)[1]}"
        there = ours.get_file_info(target)
        if there.type == pafs.FileType.File and there.size == size:
            skipped += 1
        else:
            lake_store.retrying(lambda: pafs.copy_files(path, target, source_filesystem=theirs, destination_filesystem=ours))
            copied += 1
        if ours.get_file_info(target).size != size:
            problems.append(f"{target} is not the size of its source file")
        rows += pq.read_metadata(target, filesystem=ours).num_rows
        if number % 10 == 0 or number == len(wanted):
            say(f"      {number:,} of {len(wanted):,} files ({took(started)})")
    say(f"      copied {copied:,} files; {skipped:,} were already there; {rows:,} rows in all")
    manifest = {
        "source": source, "table": name,
        "sampled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_metadata_file": None, "source_snapshot_id": None,
        "select_by": spec["select_by"],
        "source_rows": rows, "source_files": len(wanted), "source_bytes": total,
        "files_read": len(wanted), "bytes_read": total,
        "rows_kept": rows, "rows_by_facility": {}, "rows_by_load": {},
        "patients_referred_to": None, "patients_in_source": None,
        "rows_by_facility_month": [], "emptied_columns": [],
        "standin_location": f"s3://{bucket}/{src.path}",
        "problems": problems,
    }
    return manifest, problems


# -- commands --------------------------------------------------------------------

def open_sources():
    config = load_config()
    return config, {name: config.source(name) for name in {t["source"] for t in table_list()}}


def run(args) -> int:
    facilities = sampled_facilities()
    config, sources = open_sources()
    measure_only = args.command == "measure"

    catalog = fs = bucket = None
    if measure_only:
        con = duckdb.connect()  # only for the keys that file skipping needs
    else:
        if args.fresh:
            shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True, exist_ok=True)
        MANIFESTS.mkdir(exist_ok=True)
        con = duckdb.connect(str(WORK / "work.duckdb"))
        con.execute(f"SET temp_directory='{WORK / 'tmp'}'")
        bucket = standin_bucket()
        fs = standin_filesystem()
        fs.create_dir(bucket)
        catalog = SqlCatalog("standin", uri="sqlite:///:memory:", warehouse=f"s3://{bucket}", **standin_properties())
        catalog.create_namespace("standin")
    con.execute("SET memory_limit='3GB'")
    con.execute("SET preserve_insertion_order=false")

    total = table_list()
    if args.only:
        wanted = set(args.only.split(","))
        total = [t for t in total if f"{t['source']}.{t['table']}" in wanted]
        if not total:
            sys.exit(f"--only names no table in sample-tables.csv: {args.only}")
    run_started = time.time()
    to_read = 0
    for number, spec in enumerate(total, start=1):
        source, name = spec["source"], spec["table"]
        label = f"{source}.{name}"
        say(f"\n[{number}/{len(total)}] {label}")
        started = time.time()
        src = sources[source]

        if spec["select_by"] == "files":
            manifest, problems = copy_files(spec, src, measure_only)
            if manifest:
                (MANIFESTS / f"{label}.json").write_text(json.dumps(manifest, indent=2) + "\n")
            if problems:
                say("      check: " + "; ".join(problems))
                con.close()
                return 1
            continue

        table = lake_iceberg.open_table(src, name)
        local = f"{source}__{name}"
        arrow_schema = table.schema().as_arrow()
        empty = emptied_columns(source, name)
        sel = choose(con, spec, facilities, sources, rows_wanted=not measure_only)
        columns = ", ".join(f'CAST(NULL AS VARCHAR) AS "{f.name}"' if f.name in empty else f'"{f.name}"' for f in arrow_schema)
        select = f"SELECT {columns} FROM source_rows WHERE {sel['where']}"
        recipe = hashlib.md5(select.encode()).hexdigest()

        # A part-finished copy continues on the source snapshot it started with, so no file is read twice or missed.
        snapshot = table.current_snapshot()
        if not measure_only:
            saved = saved_progress(con, label)
            earlier = table.snapshot_by_id(saved[0]) if saved else None
            if saved and earlier is not None and saved[1] == recipe:
                snapshot = earlier
            else:
                forget_progress(con, label, local)

        plan = plan_files(table, snapshot, sel["prune"], sel["values"])
        share = 100 * plan["keep_bytes"] / plan["bytes"] if plan["bytes"] else 0
        to_read += plan["keep_bytes"]
        say(f"      source: {plan['rows']:,} rows in {plan['files']:,} files ({mb(plan['bytes'])})")
        say(f"      to read: {len(plan['keep']):,} files ({mb(plan['keep_bytes'])}, {share:.0f}% of the table)")
        if measure_only:
            continue

        copy_rows(con, label, local, plan, select, arrow_schema, lake_store.filesystem(src.store),
                  snapshot.snapshot_id if snapshot else 0, recipe)
        kept = con.execute(f'SELECT count(*) FROM "{local}"').fetchall()[0][0]
        say(f"      kept: {kept:,} rows ({took(started)})")

        extra = {"patients_referred_to": None, "patients_in_source": None}
        if sel["patient_keys"]:
            extra.update(patient_totals(con, spec, sel, local))
        if sel["encounters"]:
            extra.update(encounter_totals(con, spec, sel, local))

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
                          snapshot_properties={"sampler.load": str(load), "sampler.source-snapshot": str(snapshot.snapshot_id)})
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
        del back

        by_facility = {}
        if sel["facility"]:
            by_facility = {str(k): n for k, n in con.execute(
                f'SELECT "{sel["facility"]}", count(*) FROM "{local}" GROUP BY ALL ORDER BY 1').fetchall()}
        manifest = {
            "source": source, "table": name,
            "sampled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_metadata_file": table.metadata_location.rsplit("/", 1)[-1],
            "source_snapshot_id": snapshot.snapshot_id if snapshot else None,
            "select_by": spec["select_by"],
            "source_rows": plan["rows"], "source_files": plan["files"], "source_bytes": plan["bytes"],
            "files_read": len(plan["keep"]), "bytes_read": plan["keep_bytes"],
            "rows_kept": kept, "rows_by_facility": by_facility, "rows_by_load": by_load,
            **extra,
            "rows_by_facility_month": facility_month_counts(con, local, sel["facility"] if spec["select_by"] == "facility" else None, spec["load_date_column"]),
            "emptied_columns": sorted(empty),
            "standin_location": f"s3://{location}",
            "problems": problems,
        }
        (MANIFESTS / f"{label}.json").write_text(json.dumps(manifest, indent=2) + "\n")
        if problems:
            con.close()
            return 1
        forget_progress(con, label, local)  # the working copy held rows; it is in the stand-in now

    con.close()
    if measure_only:
        say(f"\nTo read in all: {mb(to_read)}. Nothing was copied.")
        return 0
    shutil.rmtree(WORK, ignore_errors=True)
    say(f"\nDone in {took(run_started)}. Working files removed. Totals are in source-sample/manifests/.")
    return 0


def verify(args) -> int:
    """Counts the same rows on the real S3 Ceph, reading every file, and compares with what was kept."""
    facilities = sampled_facilities()
    config, sources = open_sources()
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
        sel = choose(None, spec, facilities, sources)
        date_column = spec["load_date_column"]
        say(f"\n{source}.{name}: counting on the real S3 Ceph")
        _, rows = engine.run(
            f'SELECT CAST("{sel["facility"]}" AS VARCHAR), strftime(date_trunc(\'month\', "{date_column}"), \'%Y-%m\'), count(*) '
            f"FROM {source}.{name} WHERE {sel['where']} GROUP BY ALL")
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
    parser.add_argument("--only", help="comma-separated source.table names; a table chosen through another needs that one in the stand-in already")
    parser.add_argument("--fresh", action="store_true", help="forget any part-finished copy and start each table again")
    args = parser.parse_args()
    if not sampled_facilities():
        sys.exit("No row in facility_source_keys.csv has in_sample = true.")
    return verify(args) if args.command == "verify" else run(args)


if __name__ == "__main__":
    sys.exit(main())
