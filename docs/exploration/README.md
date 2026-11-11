# Exploration of the existing data lake

A record of what is in the existing DHA lake (`s3://dha-analytics`, on Ceph), written on 11 November 2026 as the starting point for building our own bronze, silver and gold layers on top of it.

## What is in this folder

| File | What it answers |
|---|---|
| [01-bucket-map.md](01-bucket-map.md) | What each folder in the bucket holds, how big and how fresh it is, and whether we need it |
| [02-source-table-inventory.md](02-source-table-inventory.md) | Every table in the five EMR source folders, with row counts, sizes and last load dates |
| [03-malaria-data-map.md](03-malaria-data-map.md) | For a disease question such as malaria: which tables supply patients, encounters, clinical notes, diagnoses, lab tests and prescriptions in each source |
| [04-rmncah-data-map.md](04-rmncah-data-map.md) | For the RMNCAH-N dashboards: which sources hold maternal, newborn, child, family planning and nutrition data, how much, and a verdict for each of the 20 core indicators |
| [table_inventory.csv](table_inventory.csv) | The inventory as a spreadsheet, including the column names of every table |

## Main findings

1. **Three folders hold the clinical data we need**, all under `iceberg/`: `hmis_kenya_emr_conso` (KenyaEMR), `hmis_ampath_prod` (AMRS) and `hmis_tiberbu_ingestion` (Tiberbu). Together they hold 151 tables, 1.9 billion rows and about 70 GB, and all three were loaded within the last few days.
2. **The lake is already a bronze layer.** The tables are a raw mirror of each source system, with the source's own column names. Nothing has been cleaned, merged or standardised.
3. **Most of the bucket is not clinical.** Of roughly 1.25 TB, about 120 GB is EMR data. The rest is mostly insurance claims and contributions.
4. **KHIS data is thin and frozen.** Only 23 indicators are present, covering July 2025 to June 2026 and not refreshed since. Most are maternal and newborn indicators, one has no data, and none is a malaria indicator. It is still the only source in the lake with national reach, with up to 7,500 facilities reporting.
5. **Tiberbu holds most of the patient-level maternal and child health data.** About 3,860 facilities have ANC, child welfare, immunisation, maternity, postnatal, nutrition and family planning records, starting in December 2024. KenyaEMR adds about 440 facilities, mostly from 2025 onwards. AMRS has very little.
6. **The KenyaEMR copy has holes.** Its `orders` table has 27,811 rows where 17.3 million are expected, and there are no usable patient, name, address, provider or test-order tables. The load history explains the first: that table was started afresh on 7 November 2026 and holds only two days of loads. Because `orders` is what ties a prescription to a patient and a date, the 8 million KenyaEMR prescriptions cannot be attributed from this copy alone.
7. **AMRS has two mismatches.** Its diagnosis table has 9,192 rows against 16 million encounters, so diagnoses must be recorded elsewhere, most likely as coded observations. And it has 21.4 million prescriptions but only 890,096 rows in `orders`, the table that should hold one parent row for each.
8. **The tables have never been tidied.** Every load appends a new small file. The Tiberbu folder alone has about 243,000 data files. There is no table catalog. Reading directly from this bucket will be slow.
9. **Repeated rows are real.** KenyaEMR's `encounter_type` lookup holds about five copies of every entry (578,124 rows for 113,205 entries), and the folder for Tiberbu's `form_data_repository` holds 30.7 million rows where the current table has 8 million. KenyaEMR's `encounter` table is far cleaner: 211,617 of its 75 million rows (0.3%) are extra copies. AMRS `encounter` showed no repeats.
10. **Sensitive content is present in clear.** Tiberbu's `patient` table holds names, phone numbers and national IDs, `doctors_notes` holds free-text clinical notes, and `company_settings` holds credential columns (`secret`, `password`, `private_key`).

## Recommendations

1. **Use the three source folders, the facility registry and the client registry as the inputs to our own bronze.** Ignore the rest of the bucket for clinical products.
2. **Copy into our own bronze rather than building on this bucket directly.** Our copy should combine the small files, record which source snapshot each row came from, and sit behind a table catalog. That removes the speed problem and gives us a stable base that does not change under us.
3. **Leave sensitive columns behind at the copy step.** Do not bring the credential columns of `company_settings` across at all, and keep names, phone numbers, national IDs and free-text notes in a restricted area.
4. **Remove repeated rows before counting anything.** Repeats have been confirmed in at least one lookup table, and some table folders hold files that are no longer part of the current table.
5. **Raise the gaps with the lake's owners** (the questions are listed below) before designing silver around tables that turn out to be incomplete.
6. **Ask for a fuller, current KHIS feed.** Both the RMNCAH-N dashboards and the malaria work depend on KHIS figures that are not in the lake today.
7. **For the malaria workshop, answer from the EMR data first.** Case-management indicators (testing, positivity, treatment, inpatient deaths) are reachable from the three sources. Elimination, stock-out and community indicators are not. The detail is in [03-malaria-data-map.md](03-malaria-data-map.md).
8. **For the RMNCAH-N dashboards, settle the indicator list and build in two layers.** The mock-ups in `resources/` show survey-based figures (under-5 mortality, stunting, contraceptive prevalence, wealth-quintile splits) that the core indicator framework set aside as not routinely collected. Of the 20 core indicators, six can be shown now from the KHIS figures in the lake and two more in part, and most of the rest can be built from Tiberbu and KenyaEMR records for the facilities on those systems. The indicator-by-indicator verdict is in [04-rmncah-data-map.md](04-rmncah-data-map.md).
9. **Bring in KNBS population projections.** Seven of the 20 RMNCAH-N indicators and the malaria incidence and mortality rates need a population denominator that is not in the lake.

## Questions for the lake's owners

1. Is `hmis_kenya_emr_conso` the current KenyaEMR copy, replacing `hmis_kenya_emr`?
2. `hmis_kenya_emr_conso/orders` was started on 7 November 2026 and holds only 27,811 rows. Will the earlier orders be backfilled?
3. In `hmis_ampath_prod`, why does `drug_order` hold 21.4 million rows when `orders` holds 890,096? Both tables were started on 11 September 2026 and have only ever been appended to.
4. Tiberbu's `form_data_repository` table was started afresh on 30 July 2026 and now holds 8 million rows, but its folder still contains older files with twice as many patients. Is the current table complete, or was data lost when it was restarted?
5. Will `patient`, `person_name`, `person_address`, `provider`, `encounter_provider`, `test_order` and the programme tables be loaded for KenyaEMR? They exist only as a partial August load.
6. How is a KenyaEMR facility database name (`source_schema`) linked to a Master Facility List code?
7. When a source row is edited, is the old version removed from the lake table or kept alongside the new one?
8. Is there a table catalog we can connect to, or is reading by folder the intended way?
9. Will the client registry (`hie_tiberbu_iceberg/client_registry`, last loaded 31 August) be refreshed?
10. Can KHIS be loaded in full and kept current, including malaria and the remaining RMNCAH-N data elements?
11. Is it intended that `company_settings` carries credential columns into the lake?

## How the exploration was done

- Read-only access with the S3 credentials in `.env`, over the VPN, using the `aws` command-line tool. Nothing in the bucket was changed.
- Folders were listed level by level. Sizes and date ranges for the non-EMR folders come from listing every object in each folder.
- For each of the 267 tables in the five EMR source folders, the newest Iceberg metadata file was downloaded and its current snapshot summary read. That gives row counts, file counts, sizes, columns and load dates without reading any patient rows.
- For the RMNCAH-N page, the `explorer` tool was used to count rows by encounter type, programme, form and month. Only totals were produced; no individual record was viewed or saved. The tool reads each table's current state, and the queries are saved in `explorer/queries/` so the counts can be repeated.

## What has not been done yet

- **No individual patient record has been examined.** The malaria page describes structure and volume only; which codes, test names and result values identify malaria is still to be confirmed, and the checks are listed at the end of [03-malaria-data-map.md](03-malaria-data-map.md). The RMNCAH-N page uses totals only.
- The tables in the non-EMR Iceberg folders (facility registry, client registry, provider portal) were sized by folder but their columns were not examined.
- The size given for `erp/` is a minimum, because its listing may have been cut short.
