# Bucket map: what each folder in `dha-analytics` holds

A folder-by-folder description of the existing lake bucket, `s3://dha-analytics`, as explored on 11 November 2026.

**How to read the sizes.** For the five EMR source folders, size is the current data only, taken from the Iceberg table definitions. For every other folder, size is the total of all objects in the folder, including old versions and bookkeeping files, so those figures run high. The `erp/` figure is a minimum: that folder has so many small files that its listing may have been cut short.

## The bucket at a glance

The bucket holds roughly 1.25 TB. About 120 GB of that is clinical EMR data. Most of the rest is health-financing data: insurance claims, provider-portal summaries and member contributions.

| Folder | What it holds | Format | Size | Loaded between | Use for clinical products? |
|---|---|---|---:|---|---|
| `iceberg/hmis_kenya_emr_conso/` | KenyaEMR, consolidated | Iceberg | 23 GB | 19 Oct to 8 Nov 2026 | **Yes, start here** |
| `iceberg/hmis_ampath_prod/` | AMPATH AMRS, production | Iceberg | 13 GB | to 11 Nov 2026 | **Yes, start here** |
| `iceberg/hmis_tiberbu_ingestion/` | Tiberbu HMIS | Iceberg | 34 GB | 9 Jul to 11 Nov 2026 | **Yes, start here** |
| `iceberg/facility_safaricom/` | Facility registry | Iceberg | 5 GB | 4 Aug to 11 Nov 2026 | Yes, as the facility list |
| `iceberg/hie_tiberbu_iceberg/` | Client registry and two related tables | Iceberg | 24 GB | August 2026 only | Yes, for patient identity; stale |
| `iceberg/hmis_kenya_emr/` | KenyaEMR, older per-facility copy | Iceberg | 33 GB | 20 Aug to 31 Oct 2026 | Only to fill gaps in the consolidated copy |
| `iceberg/hmis_ampath_uat/` | AMRS test copy | Iceberg | 16 GB | 24 to 27 Aug 2026 | No |
| `khis/` | 23 KHIS indicators, covering July 2025 to June 2026 | Parquet | 0.2 GB | 11 Jun to 8 Jul 2026 | Yes for RMNCAH-N, but few indicators and frozen |
| `iceberg/hmis_provider_portal/` | Insurance claims summaries | Iceberg and Parquet | 801 GB | 6 Oct to 11 Nov 2026 | No (financing) |
| `provider_portal/` | Earlier copy of the claims summaries | Parquet | 91 GB | 25 May to 6 Jul 2026 | No |
| `iceberg/prescription_and_dispensing/` | Prescription and authorisation summaries | Iceberg | 9 GB | 3 to 12 Jul 2026 | No |
| `claims/` | Insurance claims system tables | Parquet, JSON | 26 GB | 17 Jun to 15 Oct 2026 | No (financing) |
| `claims-uhc/` | Payer system extract and a test table | Parquet | 4 GB | 12 Jun to 15 Oct 2026 | No |
| `finsprint/` | Member coverage and contributions | Parquet | 71 GB | 8 Jun to 23 Jul 2026 | No (financing) |
| `finsprint_iceberg/` | The same three tables as Iceberg | Iceberg | 34 GB | 20 Jul to 31 Aug 2026 | No |
| `hie_finsprint/` | Earlier client-registry and facility extract | Parquet, Avro | 7 GB | 4 Jun to 3 Aug 2026 | No, superseded |
| `HIE/` | Earlier client-registry extract | Parquet | 12 GB | 10 Jun to 1 Aug 2026 | No, superseded |
| `apis/` | Earlier facility-registry extract | Parquet | under 0.1 GB | 10 Jun to 2 Aug 2026 | No, superseded |
| `erp/` | Finance system extracts (Odoo, IFS) | Parquet | 52 GB or more | 20 Jul to 11 Nov 2026 | No (financing) |
| `hmis_tiberbu_ingestion/` (top level) | Pipeline bookkeeping and early test files | JSON, Parquet | 3 GB | 15 May to 11 Nov 2026 | No |
| `hmis_ampath/` | Pipeline bookkeeping only | JSON | negligible | 24 Aug to 11 Nov 2026 | No |
| `prescription_and_dispensing/` (top level) | Four table-definition SQL files | SQL | negligible | 9 Jul 2026 | No |

There are also three stray files at the top level (a video, an image and `hello.txt`).

## The clinical sources

These are the folders that match the three source systems documented in `resources/`. Full table lists are in [02-source-table-inventory.md](02-source-table-inventory.md).

### `iceberg/hmis_kenya_emr_conso/`: KenyaEMR, consolidated

- 53 tables, 864 million rows. The largest are `obs` (690 million), `encounter` (75 million) and `visit` (22 million).
- Every table has a `source_schema` column naming the facility database the row came from.
- Loaded up to 8 November 2026.
- Two known holes: `orders` has only 27,811 rows (the older copy has 17.3 million) because that table was started afresh on 7 November 2026, and the 19 tables listed under the older copy below are absent.

### `iceberg/hmis_kenya_emr/`: KenyaEMR, older per-facility copy

- 72 tables, 1.26 billion rows, physically split by facility. 511 facility databases are present.
- 53 of its tables match the consolidated copy and stopped loading in October. It is bigger mainly because reference tables such as `concept_name` are repeated once per facility (93 million rows here, 368,000 in the consolidated copy).
- The other 19 tables exist only here, and only as a small partial load from August: `patient`, `person_name`, `person_address`, `person_attribute`, `person_attribute_type`, `provider`, `encounter_provider`, `test_order`, `procedure_order`, `conditions`, `patient_program`, `patient_state`, `program`, `program_workflow`, `program_workflow_state`, `concept_answer`, `concept_class`, `concept_datatype`, `concept_numeric`. For example `patient` has about 100,000 rows against 5.2 million in `person`.
- That the consolidated copy replaced this one is inferred from the load dates. The lake owner should confirm.

### `iceberg/hmis_ampath_prod/`: AMPATH AMRS

- 41 tables, 532 million rows. The largest are `obs` (452 million), `drug_order` (21 million), `visit` and `encounter` (16 million each).
- One database, so no facility column; facilities come from `location` joined to `facility_locations` (202 rows with facility code, county, sub-county and ward).
- Includes AMRS-specific insurance tables (`claim_visit`, `claim_line`, `claim_diagnosis`, `bill_orders`, `pre_auth_requests`).
- Most tables loaded up to 11 November 2026. Nine reference tables last loaded in September or October.

### `iceberg/hmis_ampath_uat/`: AMRS test copy

44 tables loaded over four days in August 2026 and not touched since. Ignore it.

### `iceberg/hmis_tiberbu_ingestion/`: Tiberbu HMIS

- 57 tables, 479 million rows, covering registration, appointments, queues, consultations, notes, diagnoses, lab, pharmacy, billing, claims, admissions and stock.
- One set of tables for all facilities: the `company` column is the facility, and the lake adds a `county_id` column to each table.
- Loaded up to 11 November 2026.
- The folder also contains a sub-folder named `hmis_tiberbu_ingestion.db`, which holds an older June copy of some tables. Ignore it.

## Reference data worth using

- **`iceberg/facility_safaricom/facility_registry/`** is the facility list, refreshed up to 11 November 2026. This is the natural master list for linking facilities across the three sources.
- **`iceberg/hie_tiberbu_iceberg/client_registry/`** is the national client registry, which carries the patient identifier used across systems. It was loaded only during August 2026, so it is about ten weeks behind. The same folder holds `means_inference` and `nhif_migration_record`, which appear to relate to insurance contributions and scheme migration.

## KHIS

`khis/` is small and old: 0.2 GB, loaded between 11 June and 8 July 2026. It holds 23 indicators, each with a value per facility per month for the 12 months from July 2025 to June 2026. Between 345 and 7,493 facilities report each one. One of the 23, adolescent pregnancy, has a folder but no data. The indicators are:

- **Maternal and newborn:** 8+ ANC contacts, skilled birth attendance, deliveries in health facilities, live births, facility maternal mortality, facility neonatal death rate, fresh stillbirth rate, low birth weight, newborns visited at home within 48 hours, eclampsia, obstructed labour, postpartum haemorrhage, sepsis.
- **Child and adolescent:** BCG under 1 year, measles under 1 year, adolescents 10 to 19 who are pregnant.
- **Family planning:** women of reproductive age receiving family planning commodities.
- **Other programmes:** patients currently on ARVs, cervical cancer screening (two indicators), prostate cancer screening, hypertension clients not meeting the blood pressure target, road traffic fatalities.

There is no malaria indicator, and nothing has been added since July. How each indicator lines up with the RMNCAH-N core set is in [04-rmncah-data-map.md](04-rmncah-data-map.md).

## Financing data (not needed for clinical products)

- **`iceberg/hmis_provider_portal/`** is the largest folder in the bucket at 801 GB and is still being loaded. It holds insurance claims summaries (`sha_marts`, `claims_funnel`), plus small `bed_occupancy_mart` and `user_activation_mart` tables.
- **`provider_portal/`, `iceberg/prescription_and_dispensing/`** are earlier or narrower versions of the same kind of summary.
- **`claims/`, `claims-uhc/`** are extracts of the claims and payer systems (claims, claim items, notes, patients, providers).
- **`finsprint/`, `finsprint_iceberg/`** are member coverage and contribution records.
- **`erp/`** holds finance extracts from Odoo (`account_payable_claims`, 2 GB) and IFS (`bank_payment_log`, `manual_supplier_invoice`, 50 GB). It is still being loaded and is made of about 657,000 very small files.

## Bookkeeping folders to ignore

Any folder whose name starts with an underscore is written by the loading pipeline, not by a source system: `_manifests`, `_run_manifests`, `_watermarks`, `_control`, `_progress`, `_locks`, `_checkpoints`, `_schemas`, `_ddl`, `_diag`, `_catalog`. Files named `_dagster_connectivity_probe.txt` are connection tests.

## How the lake appears to be built

These are observations from the folder contents, not statements from the lake's owners.

- **Dagster runs the loads.** Connection-test files and run records carry its name.
- **ClickHouse sits alongside the bucket.** Many folders outside `iceberg/` are named after ClickHouse tables (`..._insert_table`), their schema files use ClickHouse types, and checkpoint files are named `ceph_to_clustered_clickhouse`. Those folders look like staging for copies between the two.
- **The EMR tables are a raw mirror of each source.** Column names and types are the source's own. The only additions are `source_schema` on KenyaEMR and `county_id` on Tiberbu.
- **There is no table catalog.** Each table is a folder with `data/` and `metadata/` inside. To read one, a tool has to be pointed at the newest metadata file in that folder.
- **Loads only ever append, and nothing is tidied afterwards.** Each load adds a new small file and a new snapshot. The Tiberbu folder has about 243,000 data files across 57 tables, and a single table can carry thousands of metadata files. No table records any deletes.
