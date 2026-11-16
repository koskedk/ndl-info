#!/usr/bin/env python3
"""Why are some sampled enrolments' patients missing from the sampled patient table?

Finds the missing patient keys in the stand-in, then looks for them in the real S3 Ceph's
patient table under ANY county. Prints totals only: never a key, a name or a row.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sampler  # loads settings for both stores  # noqa: E402

import duckdb  # noqa: E402
import pyarrow.dataset as ds  # noqa: E402
from pyarrow import fs as pafs  # noqa: E402
from pyiceberg.table import StaticTable  # noqa: E402


def say(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def standin_table(path: str):
    """A stand-in table read with the read-only key."""
    s = sampler.STANDIN
    props = sampler.standin_properties() | {"s3.access-key-id": s["STANDIN_S3_ACCESS_KEY"], "s3.secret-access-key": s["STANDIN_S3_SECRET_KEY"]}
    fs = pafs.S3FileSystem(access_key=s["STANDIN_S3_ACCESS_KEY"], secret_key=s["STANDIN_S3_SECRET_KEY"],
                           endpoint_override=s["STANDIN_S3_ENDPOINT"].split("://")[1], scheme="http", force_virtual_addressing=False)
    bucket = s["STANDIN_S3_BUCKETS"].split(",")[0]
    metas = [f.path for f in fs.get_file_info(pafs.FileSelector(f"{bucket}/{path}/metadata")) if f.path.endswith(".metadata.json")]
    return StaticTable.from_metadata(f"s3://{sorted(metas)[-1]}", properties=props)


con = duckdb.connect()
con.execute("SET memory_limit='3GB'")

say("step 1 of 3: reading the two Tiberbu tables from the stand-in")
enrol = standin_table("iceberg/hmis_tiberbu_ingestion/health_program_enrollment").scan(selected_fields=("county_id", "patient", "company")).to_arrow()
pat = standin_table("iceberg/hmis_tiberbu_ingestion/patient").scan(selected_fields=("county_id", "name")).to_arrow()
con.register("enrol", enrol)
con.register("pat", pat)
con.execute("""CREATE TABLE missing AS
    SELECT DISTINCT e.county_id, e.patient AS name FROM enrol e
    WHERE NOT EXISTS (SELECT 1 FROM pat p WHERE p.county_id = e.county_id AND p.name = e.patient)""").fetchall()
total, blank = con.execute("SELECT count(*), count(*) FILTER (WHERE name IS NULL OR trim(name) = '') FROM missing").fetchall()[0]
say(f"   missing patient keys: {total:,} (of which blank: {blank:,})")
for county, n in con.execute("SELECT county_id, count(*) FROM missing GROUP BY ALL ORDER BY 2 DESC").fetchall():
    say(f"   missing, by the enrolment's county: {county}: {n:,}")
for company, n, m in con.execute("""SELECT e.company, count(DISTINCT e.patient), count(DISTINCT e.patient) FILTER (WHERE (e.county_id, e.patient) IN (SELECT county_id, name FROM missing))
                                    FROM enrol e GROUP BY ALL ORDER BY 1""").fetchall():
    say(f"   {company}: {n:,} patients referred to, {m:,} missing")

say("step 2 of 3: listing every file of the real patient table (several minutes)")
config, sources = sampler.open_sources()
src = sources["tiberbu"]
table = sampler.lake_iceberg.open_table(src, "patient")
last = [0]


def progress(done, total):
    if done - last[0] >= total // 5 or done == total:
        last[0] = done
        say(f"   load records read: {done:,} of {total:,}")


plan = sampler.lake_iceberg.current_files(src, "patient", table, on_progress=progress)
say(f"   {plan.rows:,} rows in {len(plan.files):,} files")

say("step 3 of 3: looking for the missing keys in the real table, under any county")
schema = table.schema().as_arrow()
dataset = ds.dataset(list(plan.files), filesystem=sampler.lake_store.filesystem(src.store), format="parquet", schema=schema)
con.register("source_patient", dataset)
started = time.time()
con.execute("""CREATE TABLE found AS
    SELECT DISTINCT p.name, p.county_id AS patient_county, m.county_id AS enrolment_county
    FROM source_patient p JOIN missing m ON m.name = p.name""").fetchall()
say(f"   scan finished in {time.time() - started:.0f}s")
names_found = con.execute("SELECT count(DISTINCT name) FROM found").fetchall()[0][0]
same = con.execute("SELECT count(DISTINCT name) FROM found WHERE patient_county = enrolment_county").fetchall()[0][0]
say(f"   missing keys that exist in the real patient table: {names_found:,} of {total:,}")
say(f"   ... of those, under the SAME county as the enrolment: {same:,}")
for pc, n in con.execute("SELECT patient_county, count(DISTINCT name) FROM found WHERE patient_county <> enrolment_county GROUP BY ALL ORDER BY 2 DESC LIMIT 12").fetchall():
    say(f"   ... under a different county: {pc}: {n:,}")
multi = con.execute("SELECT count(*) FROM (SELECT name FROM found GROUP BY name HAVING count(DISTINCT patient_county) > 1)").fetchall()[0][0]
say(f"   keys that appear under more than one county: {multi:,}")
say("done")
