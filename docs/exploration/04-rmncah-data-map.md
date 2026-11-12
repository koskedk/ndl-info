# Where RMNCAH-N data lives

For the RMNCAH-N dashboards (maternal, newborn, child and adolescent health, family planning and nutrition), this page says which tables and fields in the existing lake hold usable data, how much each of the three EMRs has, and which of the 20 core indicators can be answered.

All paths are under `s3://dha-analytics/`. Figures are as of 11 November 2026.

**What has been checked.** Everything here comes from totals: rows counted by encounter type, programme, form, question and answer option. No individual patient record was viewed or saved. The counts were produced with the `explorer` tool and can be repeated from the saved queries in `explorer/queries/`. They count only the rows in each table's current state.

**How far the checks go.** Table columns, encounter types, questions and form fields are all named from the data, with counts of how often each is filled in. Answer values were counted only for a handful of coded KenyaEMR questions. The values inside Tiberbu's form fields have not been read, so a field such as "Timing of Visit" is known to exist and be filled, but its answer options are not yet known.

## Short answer

| Source | What it gives for RMNCAH-N | Facilities | Period covered | Detail level |
|---|---|---:|---|---|
| **KHIS** (`khis/khis_apis_v2/`) | 22 ready-made indicators, most of them maternal and newborn | up to about 7,500 | July 2025 to June 2026, monthly | One figure per facility per month |
| **Tiberbu** (`iceberg/hmis_tiberbu_ingestion/`) | ANC, maternity, PNC, child welfare, immunisation, nutrition and family planning records | about 3,860 | December 2024 to today | Patient level |
| **KenyaEMR** (`iceberg/hmis_kenya_emr_conso/`) | ANC and PNC visits, child welfare, immunisation, labour monitoring and family planning | about 440 | Mostly 2025 and 2026 | Patient level |
| **AMRS** (`iceberg/hmis_ampath_prod/`) | Very little: a few thousand ANC and PNC visits | about 50 | 2023 to today | Patient level |

- **Tiberbu holds most of the patient-level data**, in every area: roughly ten times the facilities of KenyaEMR and the only source with delivery, newborn-unit and death-notification forms at volume.
- **The fields behind most indicators are now known in both systems.** ANC contact number, place and mode of delivery, who conducted the birth, timing of the postnatal visit, each vaccine dose, vitamin A, exclusive breastfeeding and family planning method each have a named field in Tiberbu and a named question in KenyaEMR.
- **AMRS can be left out of RMNCAH-N work.** Its current maternity forms are well designed but hold a few hundred records.
- **Of the 20 core indicators: 6 can be shown now from KHIS, 7 more can be built from records in both EMRs, 4 can probably be built from Tiberbu alone once answer values are confirmed, and 3 cannot be answered today.** The full list is in [the indicator section](#the-20-core-indicators-one-by-one).

## Where each kind of data sits

Volumes for each area, side by side. "Facilities" for KenyaEMR means facility databases; for AMRS it means locations.

| Area | Tiberbu | KenyaEMR | AMRS | Strongest source |
|---|---|---|---|---|
| **ANC** | 465,000 women enrolled in 3,862 facilities; Present Pregnancy form for 207,000 | 564,000 mother consultations (ANC and PNC together) in 442 facilities; ANC visit number recorded 301,000 times | 4,400 visits in 50 locations | Tiberbu |
| **Labour and delivery** | ChildBirth form for 62,000 mothers in 1,084 facilities; 126,000 enrolled in Maternity Forms | 71,000 labour-monitoring encounters in 142 facilities; 8,500 maternity inpatient encounters. Delivery details mostly recorded afterwards, at the postnatal or child visit | 180 deliveries in 7 locations | Tiberbu |
| **Postnatal care** | 113,000 enrolled in PNC; Postnatal Care Mother form for 38,000, Postnatal Care Child for 19,000, both with a timing-of-visit field | Postnatal visit number recorded 128,000 times in 355 facilities | 6,800 visits in 40 locations | Tiberbu |
| **Newborn care** | 69,800 patients flagged as newborns and linked to a mother; newborn unit forms for about 4,500 babies in 200 facilities (from late 2025) | 45 newborn admissions | None | Tiberbu |
| **Deaths and audits** | 4,354 death notifications, from July 2026: 22 maternal, 108 neonatal, 72 perinatal. Only 3 marked as audited | 3,100 mortality encounters with no cause or audit recorded | 15,800 death reports, all ages, from the HIV programme | Tiberbu, but thin |
| **Child growth** | 807,000 children enrolled in CWC in 3,843 facilities; Baby Weight form for 376,000 | 344,000 CWC consultations in 396 facilities | About 160 visits | Tiberbu |
| **Immunisation** | 174,000 enrolled in EPI; one form per vaccine, up to 170,000 children each, with dose and date | 128,000 immunisation encounters in 390 facilities, holding 348,000 doses | 1,950 visits in 3 locations | Tiberbu |
| **Nutrition** | 103,000 enrolled in Nutrition Services; Vitamin A form for 135,000 children; Exclusive Breastfeeding form for 62,000 | 21,000 nutrition encounters in 261 facilities; feeding method recorded 325,000 times at CWC | 163 child nutrition visits | Tiberbu |
| **Family planning** | 423,000 clients enrolled in 3,780 facilities; Family Planning form for 151,000 | 27,000 family planning encounters in 375 facilities | 700 screening visits in 4 locations | Tiberbu |
| **Adolescents** | Date of birth on `patient`, joined to any of the above | Birth date on `person`, joined to any of the above | Same, at tiny volume | Tiberbu |
| **Childhood illness** (pneumonia, diarrhoea) | Diagnoses and prescriptions, both tied to the patient | Diagnoses yes; prescriptions cannot be tied to a patient (see the malaria page) | Not a paediatric outpatient system | Tiberbu |

## KHIS

`khis/khis_apis_v2/` holds one folder per indicator. Each has a `khis_data.parquet` file with a row per facility and month: `indicator_name`, `period_id` (for example `202606`), `facility_id`, `value`, `numerator`, `denominator`. Two companion files give the facility details.

Every indicator covers the same 12 months, July 2025 to June 2026.

| Indicator in the lake | Facilities reporting | Supports core indicator |
|---|---:|---|
| Skilled birth attendance | 6,325 | RMN-02 |
| Number of deliveries in health facility | 6,325 | RMN-01, RMN-02 (denominators) |
| Live births | 6,230 | RMN-06, RMN-08, RMN-09 (denominators) |
| Pregnant women attending at least 8 ANC contacts | 4,233 | RMN-03 |
| Facility-based maternal mortality rate | 350 | RMN-01 |
| Facility-based neonatal death rate per 1,000 live births | 1,006 | RMN-06 |
| Facility-based fresh stillbirth rate | 1,528 | RMN-07 |
| Newborns visited at home within 48 hours of birth | 2,817 | RMN-08 (related, not the same measure) |
| Newborns with low birth weight (under 2,500 g) | 2,890 | context for RMN-06 |
| Under-1s receiving BCG | 6,894 | RMN-11 (one antigen only) |
| Under-1s receiving measles vaccine | 7,225 | RMN-11 (one antigen only) |
| Women of reproductive age receiving family planning commodities | 7,493 | RMN-14 |
| Eclampsia, obstructed labour, postpartum haemorrhage, sepsis | 345 to 1,939 | causes of maternal death and complications |

Also present but outside RMNCAH-N: patients on ARVs, cervical cancer screening (two indicators), prostate cancer screening, hypertension control, road traffic fatalities.

Gaps:

- **The adolescent pregnancy indicator has no data.** Its folder exists (`proportion_of_adolescents_aged_10-19_years_who_are_pregnant`) but contains only the facility files.
- **Nothing after June 2026.** The files were written on 8 July 2026 and have not been refreshed.
- **Missing altogether:** postnatal care for mothers, maternal and neonatal death audits, fully immunised child, pneumonia and diarrhoea treatment, HPV vaccination, vitamin A, exclusive breastfeeding, and malnutrition treatment outcomes.

## Tiberbu

Use `iceberg/hmis_tiberbu_ingestion`. The `company` column is the facility. Drop cancelled rows with `docstatus != 2`. Tiberbu records maternal and child health in three linked places: who is enrolled in which programme, the forms filled in at each visit, and a set of supporting tables.

### Tables and columns to use

Row counts are from the inventory taken at 17:00 on 11 November.

| Need | Table | Rows | Columns to use |
|---|---|---:|---|
| Mothers and children | `patient` | 8,743,958 | `name`, `sex`, `dob`, `custom_newborn`, `custom_parent` (links a baby to its mother), `custom_childbirth_record`, `custom_county`, `custom_sub_county`, `custom_ward` |
| Who is in which programme | `health_program_enrollment` | 2,717,037 | `program`, `patient`, `company`, `date_enrolled`, `current_state`, `completed`, `date_completed`, `episode_status` |
| What was recorded at a visit | `form_data_repository` | 7,965,818 | `form_name`, `observed_value` (all the answers, as one JSON object), `patient`, `patient_encounter`, `health_program_enrollment`, `health_program`, `company`, `creation` |
| Weight, height and MUAC | `vital_signs` | 8,064,260 | `patient`, `company`, `signs_date`, `weight`, `height`, `custom_muac`, `custom_z_score`, `custom_head_circumference` |
| Deaths and audits | `death_notification` | 4,354 | `notification_type`, `period_of_death`, `date_of_death`, `patient`, `facility_kmhfl_code`; maternal: `deceased_pregnant`, `pregnancy_timing`, `maternal_direct_cause`, `maternal_gestation_weeks`, `anc_contacts_count`, `place_of_childbirth`, `mode_of_childbirth`; perinatal: `stillborn`, `baby_outcome`, `birth_weight`, `apgar_1_min`, `apgar_5_min`, `age_at_death_days`, `perinatal_cause_category`; audit: `death_audited`, `death_audit_date`, `audit_findings`, `audit_recommendations` |
| Maternity and newborn admissions | `inpatient_record` | 370,569 | `patient`, `company`, `admitted_datetime`, `discharge_datetime`, `admission_service_unit_type`, `custom_ward`, `custom_admission_diagnosis`, `custom_discharge_diagnosis`, `custom_discharge_mode`, `custom_is_deceased` |
| Which units are maternal and newborn | `healthcare_service_unit` | 316,321 | `company`, `custom_is_mch`, `custom_is_kangaroo_mother_care`, `custom_contains_cots`, `custom_contains_incubators` |
| Pneumonia and diarrhoea in under-5s | `diagnosis_entry`, `doctor_drug_prescription` | 19,126,048 / 15,217,633 | As listed on the malaria page, joined to `patient.dob` for age |
| Facility | `company_settings` | 780,320 | `company`, `moh_khfml_code`, `dhis_id`, `county`, `sub_county`, `facility_level`. Never copy this table whole: it holds credential columns |

Counts from the supporting tables:

- **Death notifications began in July 2026.** Of 4,354 notices, 22 are marked maternal (16 facilities), 108 neonatal, 72 perinatal and 1,946 are general death certificates; 2,208 carry no type. Only 3 notices are marked as audited, and none of those is a maternal or neonatal notice.
- **Growth measures are well filled.** Of 8.1 million vital-sign readings (all ages, 5,130 facilities), 4.7 million have a weight, 2.8 million a height, 771,000 a z-score and 430,000 a MUAC (3,007 facilities).
- **Admissions cannot be picked out by department.** `medical_department` is empty on 368,000 of 370,000 admissions. Maternity and newborn admissions have to be found through the ward or service unit instead.
- **Newborns are linked to mothers.** Of 8.76 million patients, 69,800 are flagged as newborns, 69,900 are linked to a parent and 60,500 to a childbirth record. Date of birth is missing for 180,000 (2%).
- **The age groups the indicators need are well represented:** 1.98 million patients under 5, 510,000 girls aged 10 to 19 and 3.3 million women aged 15 to 49. These are people seen at a facility, not population denominators.

### Programme enrolments: `health_program_enrollment`

One row each time a patient is enrolled in a programme.

| Programme | Enrolments | Patients | Facilities | First enrolment |
|---|---:|---:|---:|---|
| CWC (child welfare clinic) | 899,000 | 807,000 | 3,843 | January 2025 |
| ANC | 577,000 | 465,000 | 3,862 | December 2024 |
| Family Planning | 443,000 | 423,000 | 3,780 | February 2025 |
| EPI (immunisation) | 182,000 | 174,000 | 3,016 | July 2025 |
| Maternity Forms | 141,000 | 126,000 | 1,762 | January 2025 |
| PNC | 117,000 | 113,000 | 2,805 | December 2024 |
| Nutrition Services | 109,000 | 103,000 | 2,374 | May 2025 |
| Neonatal | 141 | 119 | 36 | November 2026 (new) |

### Forms: `form_data_repository`

**One row is one submitted form, not one answer.** This corrects the earlier version of this page. The `form_name` column says which form it is, and `observed_value` holds every answer on that form as a single JSON object (99.9% of the 8 million rows). To read a field such as the ANC contact number, the JSON has to be unpacked. `dictionary_concept` is only a code for the form.

There are 336 forms. The ones that matter for RMNCAH-N:

| Area | Form | Submissions | Patients | Facilities | Since |
|---|---|---:|---:|---:|---|
| ANC | Present Pregnancy | 426,000 | 207,000 | 3,275 | June 2025 |
| ANC | Maternal Profile | 209,000 | 202,000 | 3,257 | December 2024 |
| ANC | Medical & Surgical History | 192,000 | 186,000 | 3,239 | December 2024 |
| ANC | Iron and Folic Acid Supplementation | 242,000 | 154,000 | 2,973 | December 2024 |
| ANC | Preventive Services | 91,000 | 79,000 | 2,722 | December 2024 |
| ANC | Malaria Prophylaxis | 107,000 | 62,000 | 947 | December 2024 |
| ANC | Antenatal Profile | 70,000 | 49,000 | 2,277 | December 2024 |
| ANC | Long Lasting Insecticidal Net | 45,000 | 41,000 | 1,579 | February 2025 |
| ANC | Maternal Serology Repeat Testing | 33,000 | 21,000 | 1,428 | December 2024 |
| ANC | Antenatal Deworming | 21,000 | 20,000 | 1,078 | March 2025 |
| Labour and delivery | ChildBirth | 76,000 | 62,000 | 1,084 | January 2025 |
| Labour and delivery | Discharge Abstract Form (mother) | 70,000 | 51,000 | 1,102 | February 2025 |
| Labour and delivery | Child Discharge Abstract Form | 70,000 | 60,000 | 1,115 | June 2025 |
| Labour and delivery | Report of Labour | 39,000 | 37,000 | 1,033 | February 2025 |
| Labour and delivery | Summary of Labour | 49,000 | 33,000 | 1,025 | February 2025 |
| Labour and delivery | WHO Labour Care Guide | 57,000 | 31,000 | 1,028 | June 2026 |
| Labour and delivery | Drugs During Labour | 24,000 | 17,000 | 840 | February 2025 |
| Labour and delivery | Foetal Heart Rate, Cervical, Contractions (partograph readings) | 30,000 to 154,000 | 13,000 to 16,000 | 760 to 890 | January 2025 |
| Postnatal | Postnatal Care Mother | 49,000 | 38,000 | 1,613 | January 2025 |
| Postnatal | PNC PHQ (depression screening) | 27,000 | 22,000 | 1,629 | July 2025 |
| Postnatal | Postnatal Care Child | 22,000 | 19,000 | 1,087 | January 2025 |
| Newborn unit | Paediatric Admission Record | 9,000 | 7,400 | 348 | October 2025 |
| Newborn unit | Newborn admission, monitoring chart and discharge forms | 5,000 to 7,300 | about 4,500 | about 200 | November 2025 to May 2026 |
| Child growth | Baby Weight | 822,000 | 376,000 | 3,376 | January 2025 |
| Child growth | Baby Height | 744,000 | 343,000 | 3,050 | January 2025 |
| Immunisation | Polio Vaccine | 258,000 | 170,000 | 2,904 | January 2025 |
| Immunisation | Rota Vaccine | 241,000 | 170,000 | 2,849 | January 2025 |
| Immunisation | Diphtheria/Pertussis/Tetanus/Hepatitis B/Hib | 235,000 | 157,000 | 2,848 | January 2025 |
| Immunisation | Pneumococcal Vaccine | 233,000 | 157,000 | 2,885 | January 2025 |
| Immunisation | Measles Vaccine | 119,000 | 110,000 | 2,811 | January 2025 |
| Immunisation | Typhoid Conjugate | 66,000 | 63,000 | 2,628 | September 2025 |
| Immunisation | IPV, IPV1 and IPV2 (three forms) | 31,000 to 56,000 | 30,000 to 54,000 | 2,230 to 2,545 | January 2025 |
| Immunisation | BCG Vaccine | 34,000 | 32,000 | 1,910 | January 2025 |
| Immunisation | Malaria Vaccines (1 - 4) | 36,000 | 28,000 | 520 | May 2025 |
| Immunisation | Yellow Fever Vaccine | 2,500 | 2,400 | 297 | August 2025 |
| Immunisation | HPV Vaccine | 500 | 470 | 262 | March 2025 |
| Nutrition | Vitamin A Supplementation | 148,000 | 135,000 | 2,750 | January 2025 |
| Nutrition | Deworming | 77,000 | 72,000 | 2,361 | January 2025 |
| Nutrition | Exclusive Breastfeeding Form | 87,000 | 62,000 | 1,553 | September 2025 |
| Nutrition | Nutrition Services | 52,000 | 37,000 | 557 | January 2025 |
| Nutrition | Nutrition Risk Screening | 36,000 | 28,000 | 784 | April 2026 |
| Family planning | Family Planning | 231,000 | 151,000 | 2,831 | December 2024 |

Three of these forms also matter for malaria: Malaria Prophylaxis (IPTp in pregnancy), Long Lasting Insecticidal Net, and Malaria Vaccines.

### Fields inside the forms

The fields inside `observed_value`, for the forms the indicators rest on. Across all 277 forms that hold answers there are 6,870 fields; the full list with fill counts is produced by `explorer/queries/tiberbu_form_fields.sql`. The number after each field is how many submissions have it filled in. These counts were taken a few hours after the table above, so the submission totals are slightly higher.

| Need | Form (submissions) | Fields to use |
|---|---|---|
| ANC contacts and measurements | Present Pregnancy (428,000) | No Of Contacts 414,000; Gestation In Weeks 219,000; Hb 428,000; Bp 428,000; Fundal Height 428,000; Muac 428,000; Next Visit Date 428,000 |
| Mother's profile | Maternal Profile (210,000) | Age 210,000; LMP 209,000; Gravida 210,000; Parity 147,000; County and Sub County 210,000 |
| ANC tests | Antenatal Profile (69,000) | Hiv 64,000; Syphilis 57,000; Hepatitis B 60,000; Rhesus 62,000; Hb for each trimester 63,000 |
| ANC preventive care | Preventive Services (91,000), Iron and Folic Acid Supplementation (243,000), Malaria Prophylaxis (108,000), Long Lasting Insecticidal Net (45,000) | Tetanus Diphtheria (TD) Injection 91,000; Supplement 238,000 and Tablets 243,000; dose 108,000; each with Date Given |
| Delivery | ChildBirth (76,900) | Date and Time 76,900; Mode of Delivery 76,900; baby Details Place Of Birth 76,900; Birth Conducted By 66,600; baby Condition 76,900; durationOfPregnancy 76,900; Complications 16,700; Mother Oxytocin 49,600 |
| Newborn at birth | ChildBirth (76,900) | baby Details Birth Weight 76,900; Apgar Score at 1, 5 and 10 min about 69,500 each; Resuscitation Done 68,600; breast Feeding Within One Hour 76,900; **baby Details Chx** (chlorhexidine) 58,600; baby Details Teo (eye ointment) 63,600; baby Details Vit K 43,500 |
| Labour summary | Summary of Labour (49,200), Report of Labour (39,700) | Mode Of Delivery 49,200; Blood Loss 49,200; Delivered By 41,600 and Designation 41,100; Cord 48,200; Mother Condition 39,700; Baby Condition 37,500 |
| Discharge after delivery | Discharge Abstract Form (70,200), Child Discharge Abstract Form (70,700) | Mother: Fate 70,200; Mode Of Delivery 64,500; Date Of Admission 67,600; Date Of Discharge 61,300. Baby: Outcome 70,700; Birth Weight Grams 70,700; Apgar scores 70,700; Date Of Discharge 61,200 |
| Postnatal check, mother | Postnatal Care Mother (49,100) | Timing of Visit 48,700; General Condition 48,800; Blood Pressure 48,700; pph 28,500; fpMethodTaken/Issued 31,600 |
| Postnatal check, baby | Postnatal Care Child (22,000) | Timing Of Contact 21,600; Date Visit 21,600; General Condition 21,900; Umbilical Cord Status 21,700; Feeding Method 21,300; Immunization Started 21,500 |
| Newborn unit | Newborn-Admission-Record-Form (5,000) | Prematurity 2,800; Lbw 2,300; Perinatal Asphyxia 1,800; Neonatal Sepsis 1,800; Jaundice 1,700; Kmc, Cpap, Oxygen and Phototherapy as yes or no |
| Growth | Baby Weight (826,000), Baby Height (749,000) | Weight 794,000; preterm 352,000; height 749,000 |
| Vaccines | One form per vaccine | dose, Date Given, timing of contact and batch number on every vaccine form. Measles Vaccine also has FullyImmunized, filled on 114,000 |
| Vitamin A and deworming | Vitamin A Supplementation (149,000), Deworming (78,000) | Dose, Date Given and Age Given, all filled |
| Breastfeeding | Exclusive Breastfeeding Form (85,600) | Ebf 85,600; Reason 4,000 |
| Malnutrition | Nutrition Services (52,400) | Nutrition Status 52,000; Patient Category 52,200; Weight In Kg 51,600; Muac 23,200; Edema 40,900; Patient Status Sam Mam 8,700; Sam Mam Details 4,800; Therapeutic Foods 12,500; Visit Type 40,300; AgeInMonths 51,900 |
| Family planning | Family Planning (230,700) | fpMethodTakenIssued 228,400; fpMethodPreferred 220,300; FirstTimeContraceptive 220,800; Fp Visit 227,700; Fp Date 230,500; Pregnancy Status 215,100; Fp Switching From 34,100 |

Things to know about the fields:

- **Field names carry a short code in front**, for example `Y5W32-No Of Contacts` or `5O3JF-baby Details Chx`. The code is part of the name and has to be matched exactly.
- **Some forms have changed their field names over time.** Newborn-Unit-Discharge has an older set of 7 fields on 7,000 submissions and a newer set of about 35 on a handful. Expect to map both.
- **The newborn unit discharge form does not yet record an outcome at volume.** The outcome and cause fields appear on only 5 submissions.
- **Personal details sit inside the forms.** Maternal Profile holds the national ID number and next-of-kin phone; ChildBirth and the discharge forms hold names. Unpack only the fields needed.
- **Reading "Chx" as chlorhexidine is an inference** from the name and from its place beside the eye ointment and vitamin K fields. Confirm it with the Tiberbu team.

**The forms table may be incomplete.** Three things point that way:

- **It was restarted.** Its load history begins on 30 July 2026, and it holds 8 million rows. Its folder still contains older files from before the restart, and counting everything in the folder gives about twice as many patients per form (for example 437,000 for Maternal Profile against 202,000 here).
- **It is out of step with programme enrolments.** 465,000 patients are enrolled in ANC, but only 202,000 have a Maternal Profile form.
- **Nothing in the table's history removed rows**, so the older files are not simply deleted records.

Treat the form counts as a lower bound until the lake's owners confirm whether the current table is complete.

## KenyaEMR

Use `iceberg/hmis_kenya_emr_conso`. KenyaEMR has no table per form. Each visit is a row in `encounter` with a type, and each answer is a row in `obs`: `concept_id` is the question, and the answer is in `value_coded`, `value_numeric`, `value_datetime` or `value_text`. So the route is: pick the encounter type, then read the `obs` rows with the concept IDs below. Join on `source_schema` plus the ID, and drop deleted rows with `voided = 0`.

The supporting tables are `person` (5,309,913 rows: `person_id`, `gender`, `birthdate`, `dead`, `death_date`, `cause_of_death`), `encounter` (74,990,769), `obs` (689,590,829) and `concept_name` (367,842, which names every question and answer).

### Encounter types and the questions to read

"Times recorded" counts rows in `obs` across all years; the number after the slash is the number of facilities. Concept IDs are in brackets.

| Need | Encounter type | Encounters (in 2026) | Facilities | Questions to read in `obs`, with times recorded |
|---|---|---:|---:|---|
| ANC enrolment | MCH Mother Enrollment | 208,000 (8,000) | 346 | Date of last menstrual period [1427] 172,000; gravida [5624] 166,000; full-term pregnancies [160080] 166,000; date of first antenatal visit [163547] 123,000; estimated date of delivery [5596] 69,000; HIV test result [159427] 204,000; syphilis test [299] 99,000 |
| ANC enrolment, new form | ANC Mother Enrollment | 59,000 (58,000) | 399 | No answers recorded. Use the encounter itself (patient, date, facility) |
| ANC and PNC visits | MCH Mother Consultation | 564,000 (123,000) | 442 | **ANC:** antenatal visit number [1425] 301,000 / 439; weeks of gestation [1438] 250,000; blood pressure [5085, 5086] 142,000; fundal height [1439] 162,000; IPTp given [1591] 80,000; daily iron [161004] 66,000; deworming [159922] 81,000; haemoglobin [21] 27,000. **PNC:** postnatal visit number [159893] 128,000 / 355; date of delivery [5599] 123,000; condition of newborn [162134] 53,000; postpartum haemorrhage [230] 57,000 |
| Delivery details | MCH Mother Consultation, CWC Enrollment, CWC Consultation, MCH Inpatient | (as listed in their own rows) | up to 425 | Method of delivery [5630] 318,000; place of birth [1572] 296,000; single or multiple birth [159949] 245,000; birth outcome, live or stillborn [159917] 41,000; mother's outcome [160085] 73,000; who assisted the delivery [1573] 24,000; birth weight [5916] 161,000; APGAR at 1, 5 and 10 minutes [159603, 159604, 159605] 19,000 each; newborn resuscitation [162131] 30,000; breastfeeding started early [161543] 26,000 |
| Labour monitoring | MCH Partograph | 71,000 (71,000) | 142 | Readings only: fetal heart rate [1440], cervical dilation [162261], contractions, pulse and blood pressure, oxytocin given [168753] 5,000. No birth outcome |
| Maternity admission | MCH Inpatient | 8,500 (8,500) | 137 | Gravida, gestation, HIV and syphilis results on about 8,000; delivery details (method, place, outcome, birth weight) on about 2,100 in 75 facilities |
| Newborn admission | New born admission | 45 (42) | 16 | APGAR scores, birth weight, danger signs. Too few to use |
| Child enrolment | CWC Enrollment | 145,000 (65,000) | 443 | Place of birth [1572] 68,000; birth weight [5916] 66,000; method of delivery [5630] 65,000; date and time infant first seen by a health worker [162140] 60,000; gestation at birth [1409] 36,000 |
| Child welfare visits | CWC Consultation | 344,000 (53,000) | 396 | Infant feeding method [1151] 325,000 / 396; weight-for-age status [1854] 181,000; height-for-age status [164088] 108,000; MUAC colour band [160908] 128,000; weight [5089] 82,000; height [5090] 77,000; developmental milestones [162069] 687,000; net received [159855] 57,000; immunisation status [164464] 84,000 |
| Vaccines given | Immunizations | 128,000 (88,000) | 390 | Which vaccine [984] 348,000; vaccination date [1410] 348,000; dose number [1418] 343,000; lot number [1420] 122,000. Each dose is a group of rows under one "immunization history" row [1421] |
| Vaccines given, old form | MCH Child Immunization | 12,000 (none) | 253 | Same questions; stopped in November 2025 |
| Nutrition | Nutrition | 21,000 (15,000) | 261 | Acute malnutrition [160205] 5,600; malnutrition type [159402] 4,500; nutritional interventions [163304] 17,000; food support [161648] 18,000 |
| Family planning | Family Planning | 27,000 (17,000) | 375 | Method [374] 32,000 / 350; family planning status [160653] 24,000; accepted family planning [159923] 15,000; commodity type [166866] 9,600; quantity given [166864] 19,000 |
| Leaving a programme | MCH Mother Discontinuation, MCH Child Discontinuation, ANC, PNC, Nutrition and Family planning Discontinuation | 30,000 / 17,000 / under 1,100 each | up to 289 | Reason for leaving [161555]; date of death [1543] |
| Deaths | Mortality | 3,100 (3,100) | 138 | Only a "transfer to" answer. No cause of death, no audit |

### What the answers look like

Counts of each answer option, for the questions the indicators rest on. These cover every encounter type in which the question is asked.

| Question | Answers recorded |
|---|---|
| Which vaccine [984] | Polio 92,000; rotavirus 57,000; pneumococcal 51,000 (plus 19,000 under an older name); DPT 37,000 and pentavalent 31,000 (two names for what is probably the same vaccine); malaria vaccine 35,000; IPV 29,000; measles-rubella 23,000; BCG 20,000; typhoid 8,000; HPV 680; yellow fever 500. The same question also holds 377,000 COVID-19 doses given to adults, 26,000 vitamin A doses, 18,000 tetanus toxoid doses and 14,000 nets |
| Place of birth [1572] | Hospital 277,000; home 9,100; health clinic 8,100; on the way to a facility 500 |
| Method of delivery [5630] | Vaginal 294,000; caesarean 21,000; assisted vaginal 2,200; breech 440 |
| Who assisted the delivery [1573] | Nurse 18,800; clinical officer or doctor 2,700; midwife 1,900; traditional birth attendant 64 |
| Birth outcome [159917] | Live birth 39,400; fresh stillbirth 519 (119 facilities); macerated stillbirth 201; miscarriage 549 |
| Mother's outcome [160085] | Alive or in good health 73,200; maternal death 61, none in 2026 |
| Condition of newborn at the postnatal visit [162134] | In good health 52,500; fair 200; died 113 |
| Infant feeding method [1151] | Exclusively breastfed 174,000 (31,000 in 2026); currently breastfeeding 66,000; mixed feeding 61,000; replacement feeding 10,000 |
| IPTp given [1591] | Yes 44,500; no 23,200; not applicable 12,500 |
| Method of family planning [374] | 2.9 million answers in all, because the question is also asked at HIV visits: condoms 1.4 million, implant 615,000, injectable 470,000, pill 46,000, tubal ligation 32,000, IUD 30,000 |

Things to know:

- **Most of this is recent.** KenyaEMR was built for HIV care; its biggest encounter types are still HIV consultation (13.7 million) and triage (11 million). The number of facilities sending data rose from about 356 in 2025 to about 514 in 2026. ANC enrolment, PNC enrolment, partograph and family planning enrolment are almost entirely 2026 data.
- **Older maternal records are mostly from the HIV programme** (prevention of mother-to-child transmission), so they describe HIV-positive mothers, not all mothers.
- **A delivery is usually recorded after the event.** There is no delivery encounter with data ("MCH Post Delivery" is empty). Method and place of birth are entered at the postnatal visit and again when the child is enrolled at the clinic, so the same birth can appear several times and may have happened at another facility. Count births per mother or per child, not per answer.
- **Four enrolment types hold no answers:** ANC Mother Enrollment, PNC Mother Enrollment, Family Planning Enrollment and Nutrition Enrollment. They still give the patient, date and facility of enrolment.
- **Two questions changed in 2026.** Exclusive breastfeeding was a yes or no question [5526] with 92,000 answers and none in 2026; it is now an answer to infant feeding method [1151]. Vitamin A was its own question [161534] with almost no 2026 answers; it is now recorded as a "vaccine" under [984]. Both versions have to be read.
- **Family planning figures from KenyaEMR lean towards HIV clients.** Only 32,000 of the 2.9 million method answers come from family planning encounters. Use the Family Planning encounter type for RMNCAH-N.
- **No question on chlorhexidine cord care was found.** The nearest is the condition of the umbilical stump (30,000 answers), which is an examination finding, not a treatment.
- **Programme tables are missing.** `patient_program` and `program` are not in the current copy. Use the enrolment encounter types instead.
- **Lookup tables contain repeats.** `encounter_type` has 578,124 rows for 113,205 real entries. About 0.3% of `encounter` rows are extra copies, and `obs` has not been checked for repeats, so these counts may be slightly high.

## AMRS

Use `iceberg/hmis_ampath_prod`. AMRS works the same way as KenyaEMR (`encounter` plus `obs`), without the facility column. It is mainly HIV care, and its RMNCAH-N content is small.

| Need | Encounter types | Encounters | Locations | Questions recorded in `obs` |
|---|---|---:|---:|---|
| ANC (from March 2023) | ANCADULTINITIAL, ANCADULTRETURN | 4,400 | 50 | Number of antenatal visits this pregnancy; weeks pregnant; estimated date of delivery; gravida; parity; tetanus dose; micronutrients provided; HIV test result |
| PNC (from March 2023) | PNCADULTINITIAL, PNCADULTRETURN | 6,800 | 40 | Postpartum visit time for mother and for baby; postnatal visit number; date, place and method of delivery; family planning method chosen |
| Labour and delivery (from March 2023) | LABORANDDELIVERY, LABORCAREGUIDE | 330 | 7 | Method of delivery; pregnancy outcome; birth weight; APGAR scores; uterotonic given; **chlorhexidine applied to cord**; kangaroo care started; breastfeeding within an hour; mother's outcome |
| Maternity stay (from June 2023) | MATERNITYADMISSION, MATERNITYDISCHARGE | 400 | 7 | Gravida, parity, antenatal visits; who conducted the delivery (free text); newborn's health status |
| Immunisation (from June 2023) | IMMUNIZATIONVISIT | 1,950 | 3 | Vaccine, date, dose number, schedule complete, vitamin A |
| Child nutrition | PEDSNUTRITION | 163 | 3 | Weight, height, z-scores, exclusively breastfed, deworming |
| Family planning | FPSCREENING | 700 | 4 | Method; family planning status |
| HIV-exposed infants | HEIFOLLOWUP | 132,000 | 165 | Infant feeding method, weight. HIV programme, so not all children |
| Deaths | DEATHREPORT | 15,800 | 170 | Date, cause and place of death. All ages, HIV programme. Maternal and perinatal death forms exist but hold 10 records |
| Older PMTCT and ANC forms | PMTCTANC, PMTCTPOSTNATAL, ANCINITIAL, ANCRETURN | 146,000 | under 90 | Stopped between 2015 and 2017 |

AMRS also has a chlorhexidine question, answered on about 160 deliveries.

## The 20 core indicators, one by one

"KHIS" means the figure is already in the lake's KHIS folder (to June 2026). The EMR columns say where the numerator can be built from patient records, for the facilities on that system. AMRS is left out of the table: it has matching fields for most maternal indicators but too few records to report.

| Indicator | KHIS in lake | Tiberbu | KenyaEMR | Verdict |
|---|---|---|---|---|
| RMN-01 Facility maternal mortality ratio | Yes | `death_notification` marked maternal (22 notices since July 2026); deliveries from the ChildBirth form | Mother's outcome holds 61 maternal deaths, none in 2026 | **Ready from KHIS.** EMR death counts are too low to trust |
| RMN-02 Skilled delivery rate | Numerator yes | ChildBirth form: Birth Conducted By (66,600) and Place Of Birth | Who assisted the delivery [1573] and place of birth [1572] | **Numerator ready from KHIS**, and can be built in both EMRs. Expected deliveries not in lake |
| RMN-03 8+ ANC contacts | Yes | Present Pregnancy form: No Of Contacts (414,000) | Antenatal visit number [1425], 301,000 answers | **Ready from KHIS**, and can be built in both EMRs. Expected pregnancies not in lake |
| RMN-04 PNC for mother within 48 hours | No | Postnatal Care Mother form: Timing of Visit (48,700) | Postnatal visit date against date of delivery [5599] | **Can be built** in both EMRs |
| RMN-05 Maternal death audit completion | No | Audit columns exist but are filled on 3 of 4,354 notices | Not recorded | **Cannot be answered.** The fields are there but unused |
| RMN-06 Facility neonatal mortality rate | Yes | 108 neonatal and 72 perinatal notices since July 2026; Child Discharge Abstract form | Newborn died at postnatal visit: 113 | **Ready from KHIS.** EMR death counts are too low to trust |
| RMN-07 Fresh stillbirth rate | Yes | ChildBirth form: baby Condition (76,900) | Birth outcome [159917]: 519 fresh stillbirths among 40,700 recorded outcomes | **Ready from KHIS**, and can be built in both EMRs |
| RMN-08 PNC for newborn within 48 hours | Related measure only | Postnatal Care Child form: Timing Of Contact (21,600) | Date and time infant first seen [162140] against date of birth | **Can be built** in both EMRs. The KHIS figure is home visits, not the same thing |
| RMN-09 Chlorhexidine cord care | No | ChildBirth form: baby Details Chx, filled on 58,600 of 76,900 births | No such question | **Can probably be built from Tiberbu**, once "Chx" is confirmed to mean chlorhexidine |
| RMN-10 Neonatal death audit completion | No | Audit columns unused, as for RMN-05 | Not recorded | **Cannot be answered** |
| RMN-11 Fully immunised child | BCG and measles only | Dose and Date Given on each vaccine form; FullyImmunized on the measles form (114,000) | Vaccine [984], dose number [1418] and date [1410] per child | **Can be built** in both EMRs, antigen by antigen. Surviving infants not in lake |
| RMN-12 Pneumonia treated with amoxicillin DT | No | Diagnoses plus prescriptions, both tied to the patient | Diagnoses yes; prescriptions cannot be tied to a patient | **Likely from Tiberbu.** Diagnosis codes and drug names still to confirm |
| RMN-13 Diarrhoea treated with ORS and zinc | No | Diagnoses plus prescriptions | As RMN-12 | **Likely from Tiberbu.** Codes and drug names still to confirm |
| RMN-14 Modern FP uptake | Yes (commodities) | Family Planning form: fpMethodTakenIssued (228,400) and FirstTimeContraceptive (220,800) | Method [374] and status [160653] in Family Planning encounters | **Proxy ready from KHIS**; numerator, split into new and continuing users, can be built from Tiberbu. Women 15 to 49 not in lake |
| RMN-15 Teenage pregnancy rate | Folder is empty | ANC enrolment plus `patient.dob` | Enrolment encounter plus `person.birthdate` | **Numerator can be built.** Girls 10 to 19 not in lake |
| RMN-16 ANC clients aged 10 to 19 | Folder is empty | ANC enrolment plus `patient.dob` | Enrolment encounter plus `person.birthdate` | **Can be built in full**: both numerator and denominator are ANC clients |
| RMN-17 HPV vaccination coverage | No | HPV Vaccine form: 470 girls | HPV as a vaccine answer: 680 doses | **Cannot be answered.** Volumes are far too low; HPV doses are probably reported elsewhere |
| RMN-18 Vitamin A supplementation | No | Vitamin A form: Dose, Date Given and Age Given (149,000) | Vitamin A under [984] and, before 2026, [161534] | **Numerator can be built** in both EMRs. Children 6 to 59 months not in lake |
| RMN-19 Exclusive breastfeeding at CWC | No | Exclusive Breastfeeding Form: Ebf (85,600, from September 2025) | Infant feeding method [1151] at CWC, with the child's age | **Can be built in full** in both EMRs |
| RMN-20 OTP default rate | No | Nutrition Services form: Patient Status Sam Mam (8,700) and Therapeutic Foods (12,500) | 5,600 acute malnutrition answers but only 84 exits recorded | **Can possibly be built from Tiberbu.** Depends on whether the status field records defaulting, which is not yet known |

In short:

- **Ready now from KHIS (6):** RMN-01, 02, 03, 06, 07 and 14. These stop at June 2026.
- **Can be built from records in both EMRs (7):** RMN-04, 08, 11, 15, 16, 18 and 19. The fields are named in Tiberbu and in KenyaEMR.
- **Probably from Tiberbu alone, once answer values are confirmed (4):** RMN-09 (the "Chx" field on the ChildBirth form), RMN-12 and 13 (pneumonia and diarrhoea codes and drug names), and RMN-20 (whether the malnutrition status field records defaulting).
- **Cannot be answered today (3):** RMN-05 and 10 (death audits are not being recorded) and RMN-17 (almost no HPV doses in either system).

## What the lake cannot supply

- **Population denominators.** Expected pregnancies, expected deliveries, surviving infants, women aged 15 to 49, girls aged 10 to 19 and children aged 6 to 59 months come from KNBS projections, which are not in the lake. Seven of the 20 indicators need them (RMN-02, 03, 11, 14, 15, 17 and 18).
- **The survey-based tiles on the dashboard mock-ups.** Under-5 mortality, stunting, wasting, contraceptive prevalence, unmet need, and the splits by wealth, education and urban or rural residence come from household surveys.
- **Community health data** (home visits, community referrals) from eCHIS.
- **National reach for patient-level indicators.** Tiberbu and KenyaEMR together cover about 4,300 facilities; KHIS reports from up to 7,500. An indicator built only from EMR records describes the facilities on those systems, not the country.

## Still to confirm

1. **The answer values inside Tiberbu's form fields.** The fields are named and counted, but their values have not been read. The ones that decide an indicator: Timing of Visit and Timing Of Contact (RMN-04, 08), baby Condition (RMN-07), baby Details Chx (RMN-09), Birth Conducted By (RMN-02), and Patient Status Sam Mam (RMN-20).
2. **Whether Tiberbu's forms table is complete.** It was restarted on 30 July 2026 and may be missing earlier records.
3. **Whether death notification is in real use.** 22 maternal deaths in four months across the Tiberbu facilities looks low, and the audit columns are empty. Ask whether audits are recorded somewhere else.
4. **Whether the KHIS figures and the EMR figures agree.** Compare a KHIS figure such as deliveries with the same count built from Tiberbu records for the same facilities and months.
5. **HPV vaccination.** About 470 girls in Tiberbu and 680 doses in KenyaEMR is far too low for routine delivery. It may be school-based and reported straight to KHIS.
6. **How Tiberbu and KenyaEMR facilities map to KHIS facility IDs**, which is needed to combine the sources. Tiberbu's `company_settings` has a `dhis_id` column for this.
7. **Whether a mother is counted in more than one system**, since women can attend facilities on different systems.
