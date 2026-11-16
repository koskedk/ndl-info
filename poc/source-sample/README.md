# The lake copy

This folder describes a small copy of DHA's data lake (S3 Ceph) that runs on this laptop, so the proof of concept can run without the VPN. The plan calls it the "stand-in S3 Ceph". This page says what is in it.

The copy holds real patient records, with names and identifiers. Handle it as confidential. `make purge` removes all of it.

## What it is

- **Where it runs:** a Docker container on this laptop (`standin-s3`), reachable only from this machine at `http://127.0.0.1:8333`.
- **What it looks like:** the same bucket name and the same folders as DHA's lake, so code written against the copy works against the real lake by changing settings only.
- **What it holds:** the records of a few chosen facilities, not the whole lake, plus the KHIS figures for the whole country. Today that is 21 tables, about 11.9 million rows, 306 MB.
- **Who can change it:** only the sampler and `make import-source`. Everything else reads it with a key that can list and read but not write.

## How it is laid out

Each source system has one folder. Each table is a folder inside it, holding the rows (`data/`) and the table's definition files (`metadata/`).

```
dha-analytics/                       the bucket
  iceberg/
    hmis_tiberbu_ingestion/          Tiberbu
      health_program_enrollment/
        data/                        the rows, one file per load
        metadata/                    the table's definition files
      form_data_repository/
      death_notification/
      patient/
    hmis_kenya_emr_conso/            KenyaEMR
      person/
      encounter/
      encounter_type/
      patient_identifier/
      patient_identifier_type/
    hmis_ampath_prod/                AMRS
      person/
      encounter/
      encounter_type/
      patient_identifier/
      patient_identifier_type/
      concept_name/
      obs/
  khis/
    khis_apis_v2/                    KHIS figures: plain files, not tables
      <run>/<indicator>/
        khis_data.parquet            one value per facility per month
        facility_details.parquet
        facility_name.parquet
```

KenyaEMR has `concept_name/` and `obs/` as well, in the same places as AMRS.

DHA's lake has more folders in the same shape: the facility and client registries. They are added to the copy when a later stage needs them.

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
| Tiberbu | `form_data_repository` | 15,516 | Every form filled in at the sampled facilities (103 kinds), one row per submitted form. The answers are in `observed_value`, as one JSON object |
| Tiberbu | `death_notification` | 16 | Death notices, with their audit fields. The facility is `hospital_of_demise` |
| Tiberbu | `patient` | 9,932 | The patients that enrolments, forms and death notices refer to, and the babies linked to them as their mother |
| KenyaEMR | `person` | 266,915 | Everyone registered at the sampled facilities |
| KenyaEMR | `encounter` | 5,545,300 | Every visit |
| KenyaEMR | `encounter_type` | 578,124 | The list of visit types, for every facility |
| KenyaEMR | `patient_identifier` | 615,320 | Patients' identifiers |
| KenyaEMR | `patient_identifier_type` | 434 | What each kind of identifier is called (National ID, CR Number and so on), per facility |
| KenyaEMR | `obs` | 2,578,992 | The answers recorded at maternal and child visits: one row per answer |
| KenyaEMR | `concept_name` | 367,842 | The names of the questions and answers in `obs`, for every facility |
| AMRS | `encounter` | 387,785 | Every encounter at the sampled locations |
| AMRS | `encounter_type` | 355 | The list of encounter types |
| AMRS | `person` | 29,816 | The patients those encounters refer to |
| AMRS | `patient_identifier` | 70,852 | Every identifier of those patients, wherever it was issued |
| AMRS | `patient_identifier_type` | 62 | What each kind of identifier is called |
| AMRS | `obs` | 353,926 | The answers recorded at maternal and child encounters |
| AMRS | `concept_name` | 124,052 | The names of the questions and answers in `obs` |
| KHIS | `khis_data` | 493,568 | One value per facility per month for 22 indicators, whole country, July 2025 to June 2026 |
| KHIS | `facility_details`, `facility_name` | 79,135 and 411,442 | The facility files that sit beside each indicator |

These are the tables the six RMNCAH-N indicators need (RMN-16, RMN-04, RMN-08, RMN-06, RMN-01 and RMN-05), plus the identifier tables the Master Patient Index starts from. Tables are repeated in the lake exactly as DHA has them, including rows that appear more than once.

Three things to know about the newer tables:

- **`obs` does not hold every answer.** It holds the answers of 178,636 KenyaEMR visits and 9,775 AMRS encounters of the types in [`visit-types.csv`](visit-types.csv). Four KenyaEMR enrolment types (ANC, PNC, Family Planning and Nutrition enrolment) record no answers at all; the visit itself is the record.
- **Tiberbu forms begin in late July 2026.** DHA's lake restarted that table then, so earlier forms are not in it.
- **A Tiberbu form can hold names, ID numbers and phone numbers** inside `observed_value`. Unpack only the fields a model needs.

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

- **Free-text notes and staff account names are left empty.** The columns are still there. This includes the free-text answer column in `obs` (`value_text`) and the audit narrative on death notices.
- **Visit answers (`obs`) are copied only for maternal and child visit types.** KenyaEMR and AMRS keep every answer in one table, mostly from HIV care. The visit types that are copied are listed in [`visit-types.csv`](visit-types.csv). The visits themselves (`encounter`) are all there; only their answers are limited.
- **Credentials are never copied.**
- **Names, phone numbers and identifiers are copied in clear**, because the Master Patient Index is built on them. They are hashed later, in silver.

Each table is written as three loads, split at 1 July and 1 October 2026 on the date each row last changed. This lets the pipeline be tested on picking up only what is new.

## One gap to know about

Many of the patients that Tiberbu records refer to are not in the copy: 3,821 of 8,374. They are missing from DHA's lake, not lost in copying. The lake's Tiberbu patient table holds only patients created or changed since late July 2026. Enrolments and forms from August 2026 onward all have their patient.

## Commands

Run these from the project folder.

| Command | What it does |
|---|---|
| `make up` | Starts the container |
| `make tables` | Lists the tables in the copy with their row counts |
| `make browse-rows` | Opens a web page for reading rows with SQL, at `http://localhost:4213` |
| `make export-source` | Writes the whole copy to one encrypted file under `exports/` |
| `make import-source FILE=...` | Replaces the copy with the contents of such a file |
| `make reset-source` | Deletes the copy only |
| `make purge` | Deletes every copy of the data on this laptop |

To look at the files in a web browser, open `http://127.0.0.1:8888/buckets/dha-analytics/iceberg/` while the container is running. The page shows folders, files and sizes, and can download a file. It cannot change anything: uploads, renames and deletes are refused.

To read rows in a web browser, run `make browse-rows` and open `http://localhost:4213`. The tables are listed on the left under `memory`, one group per system; click one to see its columns and a summary of each, or write SQL in a notebook cell. Three things to know:

- **It shows real names and identifiers.** Clicking `patient`, `person` or `patient_identifier` shows values from those columns. Close the tab and press Ctrl+C when done.
- **It needs the internet.** The page itself is downloaded from `ui.duckdb.org`; the rows never leave this laptop. Do not use the page's MotherDuck sign-in, which is a cloud service.
- **Your SQL is kept.** Notebooks are saved in `~/.duckdb` on this laptop, which `make purge` does not clear. The tables are read fresh from the stand-in each time.

## Sharing the copy

The copy is filled in one of two ways: sampled from DHA's lake over the VPN, or imported from an export that someone who sampled it has made. Teammates use the second.

- **`make export-source`** asks for a passphrase of at least 12 characters and writes `exports/standin-<date>-<time>.tar.gpg`. It prints the file's size and SHA-256.
- **`make import-source FILE=...`** asks for the passphrase, replaces the copy, and checks every table's row count against the export and against the totals in `manifests/`.

Things to know:

- **The export is the whole copy**, about the same size (310 MB today). Every import is a full replace.
- **No unencrypted copy is written to disk**, going out or coming in.
- **A wrong passphrase changes nothing.** A damaged or cut-short file is reported, and the import must then be run again.
- **Each laptop keeps its own keys.** Only the files travel.
- **If the totals differ**, the export and the project are from different days: pull the project, or ask for a newer export.
- **The export holds real patient records.** Send it only to someone cleared to hold them, over a channel approved for patient data, with the passphrase sent separately.

## Sampling from DHA's lake

This part is done by the project lead and needs the VPN. The sampling tools are not in the shared copy of this project.

| Command | What it does |
|---|---|
| `make measure` | Shows how much of each table would be read from DHA's lake. Copies nothing |
| `make sample` | Copies the tables for the listed facilities, replacing what is there. Add `ONLY=amrs.encounter,amrs.person` to copy just the named tables and leave the rest. If it stops part-way, run it again and it continues from where it stopped |
| `make verify-sample` | Counts the same rows in DHA's lake and compares |
| `make check-rules` | Checks that every text column has a rule |
| `make publish` | Copies the files listed in `ops/publish-list.txt` to the shared copy of the project |

## Files in this folder

| File | What it is |
|---|---|
| `sample-tables.csv` | Which tables are copied, and how their rows are chosen |
| `visit-types.csv` | Which visit types have their answers (`obs`) copied |
| `column-rules.csv` | How each text column is treated: identity, keep or empty |
| `source-folders.csv` | The folder each source system has in the bucket, and its short name in SQL |
| `manifests/` | One file per table with the totals from the last copy. Totals only, no records |

The sampler and its checks sit in this folder too, in the project lead's copy only.
