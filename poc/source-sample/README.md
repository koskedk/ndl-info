# The lake copy

This folder builds a small copy of DHA's data lake (S3 Ceph) on this laptop, so the proof of concept can run without the VPN. The plan calls it the "stand-in S3 Ceph". This page says what is in it.

The copy holds real patient records, with names and identifiers. Handle it as confidential. `make purge` removes all of it.

## What it is

- **Where it runs:** a Docker container on this laptop (`standin-s3`), reachable only from this machine at `http://127.0.0.1:8333`.
- **What it looks like:** the same bucket name and the same folders as DHA's lake, so code written against the copy works against the real lake by changing settings only.
- **What it holds:** the records of a few chosen facilities, not the whole lake. Today that is ten tables, about 7.5 million rows, 187 MB.
- **Who can change it:** only the sampler. Everything else reads it with a key that can list and read but not write.

## How it is laid out

Each source system has one folder. Each table is a folder inside it, holding the rows (`data/`) and the table's definition files (`metadata/`).

```
dha-analytics/                       the bucket
  iceberg/
    hmis_tiberbu_ingestion/          Tiberbu
      health_program_enrollment/
        data/                        the rows, one file per load
        metadata/                    the table's definition files
      patient/
    hmis_kenya_emr_conso/            KenyaEMR
      person/
      encounter/
      encounter_type/
      patient_identifier/
    hmis_ampath_prod/                AMRS
      person/
      encounter/
      encounter_type/
      patient_identifier/
```

DHA's lake has more folders in the same shape: the facility and client registries, and `khis/` for KHIS figures. They are added to the copy when a later stage needs them.

## Nothing is stored by facility

This is the main thing to know. There is no folder per facility or per county. Each table is one big table for all facilities, and the facility is a column in each row.

The three systems differ in how they are run at the source, and that decides which column names the facility:

| | KenyaEMR | Tiberbu | AMRS |
|---|---|---|---|
| At the source | One database per facility | One database per county | One database for all facilities |
| In the lake | All facilities merged into one table | All counties merged into one table | Copied as it is |
| The column that names the facility | `source_schema`, on every table | `company`, on some tables | `location_id`, on some tables |
| The column that names the county | None | `county_id`, on every table | None; it comes from the facility list |
| A record's ID is unique within | One facility | One county | The whole system |

Two rules follow, and both matter for every query:

1. **Always join on the scope column as well as the ID.** In KenyaEMR, patient 42 at one facility is a different person from patient 42 at another, so join on `source_schema` and the ID. In Tiberbu, join on `county_id` and the ID.
2. **Some tables have no facility column.** A Tiberbu patient row does not say which facility it belongs to. The facility comes from the records that refer to the patient, such as an enrolment.

"One database per county" for Tiberbu is read from the data, not confirmed by DHA: every table carries `county_id`, IDs repeat across counties, and each file in the lake holds exactly one county.

## What is in it now

| System | Table | Rows | What it is |
|---|---|---:|---|
| Tiberbu | `health_program_enrollment` | 13,234 | Who is enrolled in which programme (ANC, child clinic and others), where and when |
| Tiberbu | `patient` | 7,248 | The patients those enrolments refer to |
| KenyaEMR | `person` | 266,915 | Everyone registered at the sampled facilities |
| KenyaEMR | `encounter` | 5,545,300 | Every visit |
| KenyaEMR | `encounter_type` | 578,124 | The list of visit types, for every facility |
| KenyaEMR | `patient_identifier` | 615,320 | Patients' identifiers |
| AMRS | `encounter` | 387,785 | Every encounter at the sampled locations |
| AMRS | `encounter_type` | 355 | The list of encounter types |
| AMRS | `person` | 29,816 | The patients those encounters refer to |
| AMRS | `patient_identifier` | 70,852 | Every identifier of those patients, wherever it was issued |

These are the tables the first indicator needs (RMN-16, ANC clients aged 10 to 19). Tables are repeated in the lake exactly as DHA has them, including rows that appear more than once.

## Which facilities

The facilities are listed once each in the Master Facility List, [`../transform/seeds/master_facility_list.csv`](../transform/seeds/master_facility_list.csv). The name each system uses for a facility is in [`../transform/seeds/facility_source_keys.csv`](../transform/seeds/facility_source_keys.csv), and a facility is copied from a system when that row's `in_sample` is `true`.

| System | Facility | Rows of the main table |
|---|---|---:|
| Tiberbu | Lumakanda Sub County Hospital (Kakamega) | 6,434 enrolments |
| Tiberbu | Moi's Bridge Health Centre (Uasin Gishu) | 4,939 enrolments |
| Tiberbu | Turbo Sub County Hospital (Uasin Gishu) | 1,861 enrolments |
| KenyaEMR | Lumumba Sub County Hospital (Kisumu), `openmrs_lumumba` | 3,529,249 visits |
| KenyaEMR | Siaya County Referral Hospital (Siaya), `openmrs_siayacrh` | 1,553,767 visits |
| KenyaEMR | Sigomere Sub County Hospital (Siaya), `openmrs_sigomere` | 462,284 visits |
| AMRS | Kesses Health Centre (Uasin Gishu), locations 62, 195 and 333 | 124,950 encounters |
| AMRS | Moi's Bridge Health Centre (Uasin Gishu), locations 71 and 325 | 242,974 encounters |
| AMRS | Turbo Sub County Hospital (Uasin Gishu), location 329 | 19,861 encounters |

AMRS `person` and `patient_identifier` have no usable facility column, so they are taken through the patients of the sampled encounters: 29,774 patients, of whom one has no person record in DHA's lake.

## What was changed on the way in

Rows are copied as they are, with three exceptions set in [`column-rules.csv`](column-rules.csv):

- **Free-text notes and staff account names are left empty.** The columns are still there.
- **Credentials are never copied.**
- **Names, phone numbers and identifiers are copied in clear**, because the Master Patient Index is built on them. They are hashed later, in silver.

Each table is written as three loads, split at 1 July and 1 October 2026 on the date each row last changed. This lets the pipeline be tested on picking up only what is new.

## One gap to know about

About half of the patients that Tiberbu enrolments refer to are not in the copy: 3,824 of 7,391. They are missing from DHA's lake, not lost in copying. The lake's Tiberbu patient table holds only patients created or changed since late July 2026. Enrolments from August 2026 onward all have their patient.

## Commands

Run these from the `poc/` folder.

| Command | What it does |
|---|---|
| `make up` | Starts the container |
| `make measure` | Shows how much of each table would be read from DHA's lake. Copies nothing. Needs the VPN |
| `make sample` | Copies the tables for the listed facilities, replacing what is there. Needs the VPN. Add `ONLY=amrs.encounter,amrs.person` to copy just the named tables and leave the rest |
| `make verify-sample` | Counts the same rows in DHA's lake and compares. Needs the VPN |
| `make check-rules` | Checks that every text column has a rule |
| `make browse-rows` | Opens a web page for reading rows with SQL, at `http://localhost:4213` |
| `make reset-source` | Deletes the copy only |
| `make purge` | Deletes every copy of the data on this laptop |

To look inside the copy with the explorer, from `poc/`:

```
LAKE_EXPLORER_CONFIG=$PWD/source-sample/standin-sources.toml \
  uv run --project ../explorer lake-explorer tables tiberbu
```

To look at the files in a web browser, open `http://127.0.0.1:8888/buckets/dha-analytics/iceberg/` while the container is running. The page shows folders, files and sizes, and can download a file. It cannot change anything: uploads, renames and deletes are refused.

To read rows in a web browser, run `make browse-rows` and open `http://localhost:4213`. The tables are listed on the left under `memory`, one group per system; click one to see its columns and a summary of each, or write SQL in a notebook cell. Three things to know:

- **It shows real names and identifiers.** Clicking `patient`, `person` or `patient_identifier` shows values from those columns. Close the tab and press Ctrl+C when done.
- **It needs the internet the first time.** The page itself is downloaded from `ui.duckdb.org`; the rows never leave this laptop. Do not use the page's MotherDuck sign-in, which is a cloud service.
- **Nothing is saved.** Notebooks are kept in `~/.duckdb` on this laptop; the tables are read fresh from the stand-in each time.

## Files in this folder

| File | What it is |
|---|---|
| `sample-tables.csv` | Which tables are copied, and how their rows are chosen |
| `column-rules.csv` | How each text column is treated: identity, keep or empty |
| `sampler.py` | The program that does the copying |
| `check_rules.py` | The check behind `make check-rules` |
| `standin-sources.toml` | Points the explorer at the copy |
| `manifests/` | One file per table with the totals from the last copy. Totals only, no records |
| `checks/` | One-off checks, such as the one that found the patient gap |
