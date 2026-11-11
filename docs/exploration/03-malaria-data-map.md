# Where the clinical data for a disease question lives (malaria example)

For a disease such as malaria, an analysis needs six things: patients, encounters, clinical notes, diagnoses, lab tests and prescriptions. This page says which tables in the existing lake supply each one, for each of the three EMR sources.

**What has been checked.** Every table, column, row count and load date below was read from the lake's own table definitions on 11 November 2026. No patient rows were read for this page. So it confirms *where* the data sits, and does not yet confirm *which values mean malaria* (the diagnosis codes, test names, result values and drug names). Those checks are listed at the end. The one exception is the list of Tiberbu forms, which was counted later for the RMNCAH-N page and is noted below.

All paths are under `s3://dha-analytics/iceberg/`.

## Summary

| Need | KenyaEMR (`hmis_kenya_emr_conso`) | AMRS (`hmis_ampath_prod`) | Tiberbu (`hmis_tiberbu_ingestion`) |
|---|---|---|---|
| Patients | `person`, `patient_identifier` | `patient`, `person`, `patient_identifier` | `patient` |
| Encounters | `visit`, `encounter` | `visit`, `encounter` | `patient_appointment`, `patient_encounter`, `inpatient_record` |
| Clinical notes | `obs` (text values) | `obs` (text values) | `doctors_notes`, `form_data_repository` |
| Diagnoses | `encounter_diagnosis`, and coded `obs` | coded `obs` (the diagnosis table is nearly empty) | `diagnosis_entry` |
| Lab tests ordered | `orders` (see warning) | `orders` | `lab_prescription`, `lab_test` |
| Lab results | `obs` | `obs` | `normal_test_result`, `custom_lab_results` |
| Prescriptions written | `drug_order` + `orders` (see warning) | `drug_order` + `orders` (see warning) | `doctor_drug_prescription` |
| Medicines dispensed | `medication_dispense` | `pharmacy_drug_extra` | `drug_prescription`, `inpatient_medication_entry` |
| Drug list | `drug` | `drug` | `item`, `item_group` |
| Facility | `source_schema` column, `location` | `location`, `facility_locations` | `company` column, `company_settings` |
| Last loaded | 8 Nov 2026 | 11 Nov 2026 | 11 Nov 2026 |

## KenyaEMR

Use `hmis_kenya_emr_conso`. Every table carries a `source_schema` column naming the facility database the row came from (for example `openmrs_ahero`). IDs such as `patient_id` and `encounter_id` are only unique within one facility, so **every join must include `source_schema`**. Drop deleted rows with `voided = 0`.

| Need | Table | Rows | Columns to use |
|---|---|---:|---|
| Patients | `person` | 5,309,913 | `person_id`, `gender`, `birthdate`, `birthdate_estimated`, `dead`, `death_date`, `cause_of_death` |
| Patient identifiers | `patient_identifier` + `patient_identifier_type` | 10,431,742 | `patient_id`, `identifier`, `identifier_type` (the type name tells you which is the CR number / UPI, national ID, and so on) |
| Visits | `visit` + `visit_type` | 21,887,033 | `visit_id`, `patient_id`, `visit_type_id`, `date_started`, `date_stopped`, `location_id` |
| Encounters | `encounter` + `encounter_type`, `form` | 74,990,769 | `encounter_id`, `patient_id`, `visit_id`, `encounter_type`, `encounter_datetime`, `form_id`, `location_id` |
| Clinical notes | `obs` | 689,590,829 | `value_text`, `comments`, with `concept_id` saying what the note is |
| Diagnoses | `encounter_diagnosis` | 1,293,219 | `diagnosis_coded`, `diagnosis_coded_name`, `diagnosis_non_coded`, `certainty`, `dx_rank`, `encounter_id`, `patient_id` |
| Lab tests ordered | `orders` + `order_type` | 27,811 | `order_id`, `concept_id`, `order_type_id`, `date_activated`, `fulfiller_status`, `encounter_id` |
| Lab results | `obs` | (as above) | `concept_id` (the test), `value_coded` / `value_numeric` / `value_text` (the result), `order_id`, `interpretation`, `status`, `obs_datetime` |
| Prescriptions written | `drug_order` | 8,078,900 | `order_id`, `drug_inventory_id`, `dose`, `dose_units`, `frequency`, `route`, `duration`, `duration_units`, `quantity`, `drug_non_coded` |
| Medicines dispensed | `medication_dispense` | 1,484,059 | `patient_id`, `encounter_id`, `drug_id`, `drug_order_id`, `quantity`, `status`, `date_prepared`, `date_handed_over`, `location_id` |
| Drug list | `drug` | 3,204 | `drug_id`, `name`, `strength`, `dosage_form`, `concept_id` |
| Code meanings | `concept_name`, `concept_reference_map`, `concept_reference_term` | 367,842 | `concept_id` → `name`; reference terms carry the ICD codes |

Gaps and warnings:

- **There is no patient, name or address table.** `patient`, `person_name` and `person_address` are missing from this copy. The older copy (`hmis_kenya_emr`) has them, but only as a partial load from August (about 100,000 rows against 5.3 million people). Treat a patient as a `person` who has an identifier or an encounter. A patient's home county is not available; use the facility's location instead.
- **`orders` is incomplete in this copy:** 27,811 rows, against 17.3 million in the older copy (loaded to 12 October). Its load history shows the table was started afresh on 7 November 2026, so it holds only two days of loads. Until the lake owner fixes this, take lab orders from `hmis_kenya_emr/orders`, or rely on results in `obs`.
- **Prescriptions cannot be tied to a patient or a date in this copy.** A `drug_order` row holds only the drug and dosing. The patient, encounter and date sit on its parent row in `orders`, matched on `order_id`, and `orders` is the incomplete table above. Use `hmis_kenya_emr/orders` (loaded to 12 October) for that link. `medication_dispense` does not have this problem: it carries its own patient, encounter and dates.
- **Diagnoses are probably split.** 1.3 million diagnosis rows against 75 million encounters is low, which suggests many diagnoses are recorded as coded answers in `obs` rather than in `encounter_diagnosis`. This is an inference to be checked.
- **Facility code.** Nothing yet links `source_schema` to a Master Facility List code. The `global_property` table (544,511 rows, with `property` and `property_value` per facility) is the likely place to find it.

## AMPATH AMRS

Use `hmis_ampath_prod`. It is one database, so there is no `source_schema` column and IDs are unique on their own. Drop deleted rows with `voided = 0`.

| Need | Table | Rows | Columns to use |
|---|---|---:|---|
| Patients | `patient`, `person` | 1,314,743 / 1,322,157 | `person_id`, `gender`, `birthdate`, `birthdate_estimated`, `dead`, `death_date`, `cause_of_death` |
| Patient identifiers | `patient_identifier` + `patient_identifier_type` | 2,154,901 | `patient_id`, `identifier`, `identifier_type` |
| Visits | `visit` + `visit_type` | 16,473,458 | `visit_id`, `patient_id`, `visit_type_id`, `date_started`, `date_stopped`, `location_id` |
| Encounters | `encounter` + `encounter_type` | 16,383,076 | `encounter_id`, `patient_id`, `visit_id`, `encounter_type`, `encounter_datetime`, `location_id` |
| Clinical notes | `obs` | 452,340,173 | `value_text`, `comments`, `concept_id` |
| Diagnoses | `obs` (coded answers) | (as above) | `concept_id`, `value_coded` |
| Lab tests ordered | `orders` + `order_type` | 890,096 | `order_id`, `concept_id`, `order_type_id`, `date_activated`, `fulfiller_status` |
| Lab results | `obs` | (as above) | `concept_id`, `value_coded` / `value_numeric` / `value_text`, `order_id`, `status` |
| Prescriptions written | `drug_order` | 21,367,393 | `order_id`, `drug_inventory_id`, `dose`, `dose_units`, `frequency`, `route`, `duration`, `quantity`, `drug_non_coded` |
| Medicines dispensed | `pharmacy_drug_extra` | 92,080 | `patient_id`, `drug_id`, `drug_name`, `quantity_sold`, `encounter_uuid`, `encounter_date`, `location_uuid`, `total_amount` |
| Drug list | `drug` | 3,308 | `drug_id`, `name`, `strength`, `dosage_form`, `concept_id` |
| Facility | `location` → `facility_locations` | 563 / 202 | `location_uuid` → `facility_code`, `facility_name`, `county`, `sub_county`, `ward`, `facility_level` |

Gaps and warnings:

- **`encounter_diagnosis` holds only 9,192 rows** against 16.4 million encounters, so it is not where AMRS diagnoses live. Expect them in `obs`. `claim_diagnosis` (2,963 rows, with an `icd_code` column) covers insurance claims only.
- **Most prescriptions have no parent order.** `drug_order` has 21.4 million rows but `orders`, which holds the patient, encounter and date for each one, has only 890,096 rows in total across all order types. Either `orders` is incomplete or `drug_order` contains repeats. Until that is settled, AMRS prescriptions cannot be reliably tied to patients.
- **Dispensing records are sparse.** `pharmacy_drug_extra` has 92,080 rows, far fewer than the prescriptions, so it likely covers only some facilities or only paid dispensing.
- **No names or addresses** are in the lake for AMRS. A patient's home county is not available; the facility's county comes from `facility_locations`.
- AMRS is the only source with a ready-made link from location to facility code and county.

## Tiberbu

Use `hmis_tiberbu_ingestion`. One set of tables holds all facilities: the `company` column is the facility, and the lake adds a `county_id` column to every table. Keys are text (for example `HLC-PAT-2025-00042`). Drop cancelled rows with `docstatus != 2`. Child tables link to their parent through `parent` and `parenttype`.

| Need | Table | Rows | Columns to use |
|---|---|---:|---|
| Patients | `patient` | 8,707,251 | `name`, `sex`, `dob`, `status`, `custom_patient_upi`, `custom_county`, `custom_sub_county`, `custom_ward`, `custom_deceased`, `custom_death_date`, `custom_newborn` |
| Visits | `patient_appointment` | 13,260,171 | `name`, `patient`, `company`, `appointment_date`, `appointment_type`, `department`, `status` |
| Consultations | `patient_encounter` | 25,288,421 | `name`, `patient`, `appointment`, `company`, `encounter_date`, `medical_department`, `inpatient_record`, `custom_visit_disposition` |
| Admissions | `inpatient_record` | 369,311 | `patient`, `admitted_datetime`, `discharge_datetime`, `custom_admission_diagnosis`, discharge mode and deceased flags |
| Deaths | `death_notification` | 4,335 | `patient`, `date_of_death`, `immediate_cause`, `underlying_cause` |
| Clinical notes | `doctors_notes` | 27,174,062 | `patient`, `patient_encounter`, `notes_date`, `subjective`, `objective`, `assessment`, `plan`, `history_of_presenting_illness`, `provisional_diagnosis` |
| Structured form answers | `form_data_repository` | 7,931,765 | `form_name`, `dictionary_concept`, `observed_value`, `patient`, `patient_encounter` |
| Malaria prevention forms | `form_data_repository` | (within the above) | `form_name` is one of: Malaria Prophylaxis (about 62,000 patients, 947 facilities), Long Lasting Insecticidal Net (41,000 patients, 1,579 facilities), Malaria Vaccines (1 - 4) (28,000 patients, 520 facilities). These are lower bounds: the forms table may be incomplete, as explained on the RMNCAH-N page. |
| Diagnoses | `diagnosis_entry` | 19,052,080 | `parent` (the encounter), `diagnosis_code`, `description`, `status`, `suspected`, `is_primary`, `confirmed_via`, `confirmed_on` |
| Diagnosis code lists | `codification_table`, `description_reports_mapping` | 271,265 / 6,809 | `code_system`, `code`, `display`; `description` → `distinctive_diseases`, `report_type` |
| Lab tests ordered | `lab_prescription` | 3,734,322 | `parent` (the encounter), `lab_test_name`, `lab_test_code`, `custom_suspected_diagnosis`, `custom_point_of_care_test` |
| Lab tests done | `lab_test` | 3,768,904 | `name`, `patient`, `company`, `lab_test_name`, `template`, `status`, `date`, `result_date`, `approved_date`, `custom_patient_encounter` |
| Lab results | `normal_test_result`, `custom_lab_results` | 48,053,458 / 2,290,030 | `parent` (the lab test), `lab_test_name`, `result_value`, `normal_range`, `custom_result_implication` |
| Prescriptions written | `doctor_drug_prescription` | 15,173,840 | `parent` (the encounter), `patient`, `drug`, `drug_name`, `dose`, `route_of_administration`, `frequency`, `duration`, `start_date`, `status`, `to_dispense`, `is_discharge_medication`, `is_pediatric_dose`, `patient_weight_kg` |
| Medicines dispensed | `drug_prescription` | 13,165,448 | `parent` (the encounter or inpatient record), `drug_code`, `drug_name`, `strength`, `dosage_form`, `custom_status`, `custom_qty`, `custom_doctors_prescription` (link back to the doctor's order) |
| Inpatient medication | `inpatient_medication_order`, `inpatient_medication_entry` | 564,880 / 156,046 | `patient`, `inpatient_record`, `company`, `start_date`, `status`; `item_code`, `posting_date` |
| Drug list | `item`, `item_group` | 17,697,125 / 18,680 | `item_code`, `item_name`, `item_group`; `custom_is_prescription_item`, `custom_report_drug_type` |
| Facility | `company_settings` | 778,775 | `company`, `moh_khfml_code`, `facility_registry_identifier`, `dhis_id`, `county`, `sub_county`, `facility_level` |

Gaps and warnings:

- **Tiberbu is the richest source for a disease question.** It is the only one with a dedicated notes table, a patient home county, and a "confirmed via" field on the diagnosis.
- **Prescribing and dispensing are separate and linked.** `doctor_drug_prescription` is what the doctor ordered and carries the patient directly. `drug_prescription` is what the pharmacy dispensed, with `custom_status` (Pending, Dispensed, Paused, Cancelled) and a link back to the doctor's order. That makes "prescribed but not dispensed" answerable here, which it is not in the other two sources.
- **The drug list is very large.** `item` has 17.7 million rows, which suggests one copy per facility or repeated loads. Expect to de-duplicate it before using it as a drug list.
- **Personal details are stored in clear** in `patient` (names, phone, national ID) and in the free text of `doctors_notes`. Handle with care and keep them out of anything shared.
- **`company_settings` contains credential columns** (`secret`, `password`, `private_key`, `consumer_key`). Select only the facility columns listed above and never copy the table whole.
- `description_reports_mapping` appears to map diagnosis descriptions to reporting categories, which may give a ready-made "malaria" grouping. To be checked.

## What the lake cannot answer for malaria

These come from systems that are not in the lake today:

- **KHIS malaria figures.** The lake holds only 23 KHIS indicators, loaded in June and July 2026, and none is a malaria indicator.
- **Elimination (1-3-7) indicators**, which come from the KHIS case-based surveillance tracker.
- **Commodity stock-outs** (AL, mRDTs, injectable artesunate), which come from KHIS LMIS. The EMRs hold facility stock tables, which are not the same thing.
- **Community testing by CHPs**, which comes from eCHIS.
- **Population denominators** for incidence and mortality, which come from KNBS projections.

From the EMR data alone, two groups of malaria indicators in the core framework are reachable:

- **Case management, from all three sources:** test positivity (MAL-07), suspected cases tested (MAL-10, MAL-12), confirmed cases treated with ACT (MAL-13), inpatient case fatality (MAL-04), and the case and death counts behind incidence and mortality (MAL-01, MAL-02).
- **Prevention, from Tiberbu's forms:** nets issued at ANC and child welfare clinics (MAL-05, MAL-06), IPTp doses in pregnancy (MAL-08) and malaria vaccine doses (MAL-09). These cover the facilities on Tiberbu only, and which fields hold the dose number and date still has to be confirmed.

## Still to confirm by reading data

1. **Which codes mean malaria.** In KenyaEMR and AMRS, find the malaria concepts in `concept_name`. In Tiberbu, find the malaria rows in `diagnosis_entry` (ICD-10 B50 to B54, ICD-11 1F40 to 1F4Z, and free-text descriptions).
2. **Which tests are malaria tests** (mRDT, blood slide for malaria parasites) and how a positive result is written, in each source.
3. **Which drugs are antimalarials** (artemether-lumefantrine and other ACTs, injectable artesunate, SP for IPTp) in `drug`, `item` and the free-text drug name columns.
4. **Whether prescriptions can be tied to patients** in KenyaEMR and AMRS, given the gaps in `orders`.
5. **Where KenyaEMR and AMRS diagnoses really sit**: `encounter_diagnosis` or coded `obs`.
6. **Duplicates.** The tables are loaded by appending, with no deletes recorded. A source row that was edited may therefore appear more than once. Check for repeated primary keys before counting anything.
7. **Facility linkage** for KenyaEMR: `source_schema` to Master Facility List code.
8. **Volumes**: malaria diagnoses, tests and treatments per source per month, to show the workshop what is really there.
