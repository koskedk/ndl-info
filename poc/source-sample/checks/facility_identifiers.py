#!/usr/bin/env python3
"""Looks up FID, MFL code, level and ownership in DHA's lake for the facilities on the Master Facility List.

Reads facility reference columns only: no patient data, no credential columns, no people's names.
Sources: Tiberbu company_settings, AMRS facility_locations, and DHA's facility registry as a cross-check.
"""
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sampler  # noqa: E402

import duckdb  # noqa: E402
import pyarrow.dataset as ds  # noqa: E402


def say(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def source_dataset(src, table_name, column=None, values=()):
    table = sampler.lake_iceberg.open_table(src, table_name)
    plan = sampler.plan_files(table, column, list(values))
    say(f"   {table_name}: reading {len(plan['keep']):,} of {plan['files']:,} files ({sampler.mb(plan['keep_bytes'])})")
    schema = table.schema().as_arrow()
    return ds.dataset(plan["keep"], filesystem=sampler.lake_store.filesystem(src.store), format="parquet", schema=schema)


facilities = sampler.sampled_facilities()
config = sampler.load_config()
con = duckdb.connect()
out = Path(__file__).resolve().parent.parent / "manifests" / "facility_identifiers.csv"
rows = []

say("step 1 of 3: Tiberbu company_settings")
tib = facilities["tiberbu"]
con.register("cs", source_dataset(config.source("tiberbu"), "company_settings", "county_id", sorted(tib["counties"])))
found = con.execute(f"""
    SELECT company, county_id, facility_registry_identifier, moh_khfml_code, dhis_id, facility_level, facility_ownership, sub_county
    FROM (SELECT *, row_number() OVER (PARTITION BY county_id, company ORDER BY modified DESC) AS rn
          FROM cs WHERE company IN {sampler.in_list(tib['keys'])} AND county_id IN {sampler.in_list(sorted(tib['counties']))})
    WHERE rn = 1 ORDER BY company""").fetchall()
for company, county, fid, mfl, dhis, level, owner, sub in found:
    rows.append(dict(source_system="tiberbu", source_facility_key=company, fid=fid, mfl_code=mfl, khis_id=dhis, level=level, ownership=owner, sub_county=sub, name=company))
say(f"   found {len(found)} of {len(tib['keys'])} facilities")

say("step 2 of 3: AMRS facility_locations")
amrs = facilities["amrs"]
con.register("fl", source_dataset(config.source("amrs"), "facility_locations"))
found = con.execute(f"""
    SELECT DISTINCT CAST(location_id AS VARCHAR), fr_code, facility_code, facility_level, facility_name, sub_county
    FROM fl WHERE CAST(location_id AS VARCHAR) IN {sampler.in_list(amrs['keys'])} ORDER BY 1""").fetchall()
for loc, fid, mfl, level, name, sub in found:
    rows.append(dict(source_system="amrs", source_facility_key=loc, fid=fid, mfl_code=mfl, khis_id="", level=level, ownership="", sub_county=sub, name=name))
say(f"   found {len(found)} of {len(amrs['keys'])} locations")

say("step 3 of 3: DHA facility registry, as a cross-check on every FID (about 3 minutes)")
listed = {r["fid"] for r in csv.DictReader(sampler.FACILITIES.open()) if r["fid"]}
fids = sorted({r["fid"] for r in rows if r["fid"]} | listed)
con.register("reg", source_dataset(config.source("facility"), "facility_registry"))
registry = con.execute(f"""
    SELECT frCode, officialName, kephLevel, facilityOwnership, address_county, address_subCounty
    FROM (SELECT *, row_number() OVER (PARTITION BY frCode ORDER BY internal_ingestion_timestamp DESC) AS rn
          FROM reg WHERE frCode IN {sampler.in_list(fids)})
    WHERE rn = 1 ORDER BY frCode""").fetchall()
say(f"   {len(registry)} of {len(fids)} FIDs are in the registry")

with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["where", "source_system", "source_facility_key", "fid", "mfl_code", "khis_id", "level", "ownership", "sub_county", "name", "county"])
    for r in rows:
        w.writerow(["source", r["source_system"], r["source_facility_key"], r["fid"], r["mfl_code"], r["khis_id"], r["level"], r["ownership"], r["sub_county"], r["name"], ""])
    for fid, name, level, owner, county, sub in registry:
        w.writerow(["registry", "", "", fid, "", "", level, owner, sub, name, county])
say(f"written to {out.name}")
print()
for line in out.read_text().splitlines():
    print(line)
