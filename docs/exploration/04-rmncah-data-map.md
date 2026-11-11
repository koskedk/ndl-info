# Where RMNCAH-N data lives

For the RMNCAH-N dashboards (maternal, newborn, child and adolescent health, family planning and nutrition), this page says which parts of the existing lake hold usable data, how much, and for how many facilities. It ends with a line for each of the 20 core RMNCAH-N indicators.

All paths are under `s3://dha-analytics/`. Figures are as of 11 November 2026.

**What has been checked.** Unlike the malaria page, this one is based on reading data, but only as totals: counts by encounter type, programme, form and month. No individual patient record was viewed or saved. The counts were produced with the `explorer` tool on 11 November 2026 and can be re-run from the saved queries in `explorer/queries/`. They count only the rows in each table's current state.

One caution on Tiberbu's forms table, explained in its section below: the current table may be incomplete.

## Short answer

| Source | What it gives for RMNCAH-N | Facilities | Period covered | Detail level |
|---|---|---:|---|---|
| **KHIS** (`khis/khis_apis_v2/`) | 22 ready-made indicators, most of them maternal and newborn | up to about 7,500 | July 2025 to June 2026, monthly | One figure per facility per month |
| **Tiberbu** (`iceberg/hmis_tiberbu_ingestion/`) | ANC, maternity, PNC, child welfare, immunisation, nutrition and family planning records | about 3,860 | December 2024 to today | Patient level |
| **KenyaEMR** (`iceberg/hmis_kenya_emr_conso/`) | ANC, child welfare, immunisation, labour and family planning encounters | about 440 | Mostly 2025 and 2026 | Patient level |
| **AMRS** (`iceberg/hmis_ampath_prod/`) | Very little: a few thousand ANC and PNC visits | about 50 | 2023 to today | Patient level |

- **For national dashboard figures, KHIS is the only source with national reach**, but what is in the lake stops at June 2026 and covers 22 indicators.
- **For patient-level detail and anything KHIS does not carry, Tiberbu is the main source.** It has the most facilities, purpose-built maternal and child forms, and is loaded daily.
- **KenyaEMR adds a further 440 or so facilities**, with the detail held in observations rather than in named forms.
- **AMRS can be left out of RMNCAH-N work.** It is mainly an HIV care system.

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

Tiberbu records maternal and child health in three linked places.

### 1. Programme enrolments: `health_program_enrollment`

One row each time a patient is enrolled in a programme. Columns: `program`, `patient`, `company` (the facility), `date_enrolled`, `current_state`, `completed`, `date_completed`, `episode_status`.

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

### 2. Structured form answers: `form_data_repository`

One row per answered question on a form. Columns: `form_name`, `dictionary_concept` (the question), `observed_value` (the answer), `patient`, `patient_encounter`, `health_program_enrollment`, `company`. This is where the clinical content of an ANC visit, a delivery or an immunisation sits.

There are 336 forms in all. The largest ones for RMNCAH-N, by number of patients with at least one record:

| Area | Form | Patients | Facilities |
|---|---|---:|---:|
| ANC | Present Pregnancy | 207,000 | 3,275 |
| ANC | Maternal Profile | 202,000 | 3,257 |
| ANC | Medical & Surgical History | 186,000 | 3,239 |
| ANC | Iron and Folic Acid Supplementation | 154,000 | 2,973 |
| ANC | Preventive Services | 79,000 | 2,722 |
| ANC | Malaria Prophylaxis | 62,000 | 947 |
| ANC | Antenatal Profile | 49,000 | 2,277 |
| ANC | Long Lasting Insecticidal Net | 41,000 | 1,579 |
| ANC | Maternal Serology Repeat Testing | 21,000 | 1,428 |
| Labour and delivery | ChildBirth | 62,000 | 1,084 |
| Labour and delivery | Child Discharge Abstract Form | 60,000 | 1,115 |
| Labour and delivery | Discharge Abstract Form | 51,000 | 1,102 |
| Labour and delivery | Report of Labour | 37,000 | 1,033 |
| Labour and delivery | Summary of Labour | 33,000 | 1,025 |
| Labour and delivery | WHO Labour Care Guide (from June 2026) | 31,000 | 1,028 |
| Labour and delivery | Foetal Heart Rate, Cervical, Contractions (partograph readings) | 13,000 to 16,000 | 760 to 890 |
| Postnatal | Postnatal Care Mother | 38,000 | 1,613 |
| Postnatal | PNC PHQ (depression screening) | 22,000 | 1,629 |
| Postnatal | Postnatal Care Child | 19,000 | 1,087 |
| Newborn unit | Newborn admission, monitoring chart and discharge forms | about 4,500 | about 200 |
| Newborn unit | Paediatric Admission Record (from October 2025) | 7,400 | 348 |
| Child growth | Baby Weight | 376,000 | 3,376 |
| Child growth | Baby Height | 343,000 | 3,050 |
| Immunisation | Rota Vaccine | 170,000 | 2,849 |
| Immunisation | Polio Vaccine | 170,000 | 2,904 |
| Immunisation | Diphtheria/Pertussis/Tetanus/Hepatitis B/Hib | 157,000 | 2,848 |
| Immunisation | Pneumococcal Vaccine | 157,000 | 2,885 |
| Immunisation | Measles Vaccine | 110,000 | 2,811 |
| Immunisation | Typhoid Conjugate | 63,000 | 2,628 |
| Immunisation | IPV | 52,000 | 2,464 |
| Immunisation | BCG Vaccine | 32,000 | 1,910 |
| Immunisation | Malaria Vaccines (1 - 4) | 28,000 | 520 |
| Immunisation | Yellow Fever Vaccine | 2,400 | 297 |
| Immunisation | HPV Vaccine | 470 | 262 |
| Nutrition | Vitamin A Supplementation | 135,000 | 2,750 |
| Nutrition | Deworming | 72,000 | 2,361 |
| Nutrition | Exclusive Breastfeeding Form (from September 2025) | 62,000 | 1,553 |
| Nutrition | Nutrition Services | 37,000 | 557 |
| Family planning | Family Planning | 151,000 | 2,831 |

**The forms table may be incomplete.** Three things point that way:

- **It was restarted.** Its load history begins on 30 July 2026, and it holds 8 million rows. Its folder still contains older files from before the restart, and counting everything in the folder gives about twice as many patients per form (for example 437,000 for Maternal Profile against 202,000 here).
- **It is out of step with programme enrolments.** 465,000 patients are enrolled in ANC, but only 202,000 have a Maternal Profile form.
- **Nothing in the table's history removed rows**, so the older files are not simply deleted records.

Treat the form counts as a lower bound until the lake's owners confirm whether the current table is complete.

Three of these forms also matter for malaria: Malaria Prophylaxis (IPTp in pregnancy), Long Lasting Insecticidal Net, and Malaria Vaccines.

### 3. Supporting tables

| Table | Rows | RMNCAH-N content |
|---|---:|---|
| `patient` | 8,707,251 | `dob`, `sex`, `custom_newborn`, `custom_parent` (links a baby to its mother), `custom_childbirth_record`, county, sub-county and ward |
| `death_notification` | 4,335 | Maternal fields (`deceased_pregnant`, `pregnancy_timing`, `maternal_direct_cause`, `maternal_gestation_weeks`, `anc_contacts_count`), perinatal fields (`stillborn`, `birth_weight`, `apgar_1_min`, `apgar_5_min`), and audit fields (`death_audited`, `death_audit_date`, `audit_findings`) |
| `vital_signs` | 8,049,816 | `weight`, `height`, `custom_muac`, `custom_z_score`, `custom_head_circumference` |
| `queue_state_movements` | 27,557,523 | `anc_opd` flag on a service-point visit |
| `healthcare_service_unit` | 315,333 | Flags for MCH units, kangaroo mother care, cots and incubators |
| `diagnosis_entry`, `doctor_drug_prescription` | 19 M / 15 M | Pneumonia and diarrhoea diagnoses in under-5s and what was prescribed |
| `inpatient_record` | 369,311 | Maternity and newborn admissions and discharge outcomes |

## KenyaEMR

KenyaEMR has no table per form. Each visit is an `encounter` with a type, and the answers are rows in `obs`. So the route is: pick the encounter types below, then read the `obs` rows for those encounters. The questions and answers are concept IDs, named in `concept_name`.

Encounters by type, excluding deleted rows, rounded.

| Encounter type | Encounters | Of which in 2026 | Facilities |
|---|---:|---:|---:|
| MCH Mother Consultation (ANC and PNC visits) | 564,000 | 123,000 | 442 |
| CWC Consultation | 344,000 | 53,000 | 396 |
| MCH Mother Enrollment | 208,000 | 8,000 | 346 |
| CWC Enrollment | 145,000 | 65,000 | 443 |
| Immunizations | 128,000 | 88,000 | 390 |
| MCH Child HEI Exit (HIV-exposed infants) | 73,000 | 2,000 | 252 |
| MCH Partograph (labour) | 71,000 | 71,000 | 142 |
| ANC Mother Enrollment | 59,000 | 58,000 | 399 |
| Family Planning | 27,000 | 17,000 | 375 |
| Nutrition | 21,000 | 15,000 | 261 |
| PNC Mother Enrollment | 19,000 | 19,000 | 324 |
| Family Planning Enrollment | 18,000 | 18,000 | 305 |
| MCH Inpatient (from December 2025) | 8,500 | 8,500 | 137 |
| Nutrition Enrollment | 6,500 | 6,400 | 174 |
| Mortality | 3,100 | 3,100 | 138 |
| New born admission | 45 | 42 | 16 |

The table holds 74.3 million encounters in all, loaded up to 7 November 2026. About 0.3% of its rows are extra copies of the same encounter, so these counts are very slightly high.

Things to know:

- **Most of this is recent.** KenyaEMR was built for HIV care; its biggest encounter types are still HIV consultation (13.7 million) and triage (11 million). The number of facilities sending data rose from about 356 in 2025 to about 514 in 2026, and encounters roughly doubled. ANC enrolment, PNC enrolment, partograph and family planning enrolment are almost entirely 2026 data.
- **Older maternal records are mostly from the HIV programme** (prevention of mother-to-child transmission), so they describe HIV-positive mothers, not all mothers.
- **No delivery encounter was found.** A type named "MCH Post Delivery" exists but has no encounters. Births appear to be recorded through MCH Partograph and MCH Inpatient; this needs confirming in `obs`.
- **Programme tables are missing.** `patient_program` and `program`, which would list who is enrolled in MCH-Mother and MCH-Child, are not in the current copy. Use the enrolment encounter types above instead.
- **Lookup tables contain repeats.** `encounter_type` has 578,124 rows for 113,205 real entries, about five copies of each. De-duplicate lookups before joining to them.

## AMRS

AMRS is mainly HIV care; its largest encounter types are adult and paediatric HIV return visits. RMNCAH-N content is small:

| Encounter type | Encounters | Locations | Notes |
|---|---:|---:|---|
| ANC (adult initial and return) | 4,400 | 50 | from March 2023 |
| PNC (adult initial and return) | 6,800 | 40 | from March 2023 |
| Immunization visit | 1,900 | 3 | from June 2023 |
| Maternity admission and discharge | 400 | 7 | from June 2023 |
| Labour and delivery | 180 | 7 | from March 2023 |
| Older PMTCT and ANC forms | 150,000 | under 90 | stopped between 2015 and 2019 |

No sign of repeated encounter rows was found in AMRS.

## The 20 core indicators, one by one

"KHIS" means the figure is already in the lake's KHIS folder (to June 2026). "Tiberbu" and "KenyaEMR" mean it can be worked out from patient records for the facilities on those systems.

| Indicator | KHIS in lake | Tiberbu | KenyaEMR | Verdict |
|---|---|---|---|---|
| RMN-01 Facility maternal mortality ratio | Yes | `death_notification` maternal fields | Mortality encounters | Ready from KHIS |
| RMN-02 Skilled delivery rate | Numerator yes | ChildBirth form | Partograph, MCH Inpatient | Numerator ready; expected deliveries not in lake |
| RMN-03 8+ ANC contacts | Yes | ANC enrolment and forms | MCH Mother Consultation | Ready from KHIS; expected pregnancies not in lake |
| RMN-04 PNC for mother within 48 hours | No | Postnatal Care Mother form | PNC enrolment, MCH Mother Consultation | EMR only |
| RMN-05 Maternal death audit completion | No | `death_notification` audit fields | Not found | Tiberbu only |
| RMN-06 Facility neonatal mortality rate | Yes | `death_notification`, Child Discharge Abstract | Mortality encounters | Ready from KHIS |
| RMN-07 Fresh stillbirth rate | Yes | `death_notification.stillborn`, ChildBirth form | Not confirmed | Ready from KHIS |
| RMN-08 PNC for newborn within 48 hours | Related measure only | Postnatal Care Child form | CWC forms | KHIS figure is home visits, not the same thing |
| RMN-09 Chlorhexidine cord care | No | No form of its own; would be a field inside ChildBirth or Postnatal Care Child | Not confirmed | To be checked at field level |
| RMN-10 Neonatal death audit completion | No | `death_notification` audit fields | Not found | Tiberbu only |
| RMN-11 Fully immunised child | BCG and measles only | All routine vaccine forms | Immunizations encounters | Has to be built from EMR vaccine records |
| RMN-12 Pneumonia treated with amoxicillin DT | No | Diagnoses plus prescriptions | Diagnoses plus prescriptions (see prescriptions gap) | Tiberbu first |
| RMN-13 Diarrhoea treated with ORS and zinc | No | Diagnoses plus prescriptions | Diagnoses plus prescriptions (see prescriptions gap) | Tiberbu first |
| RMN-14 Modern FP uptake | Yes (commodities) | Family Planning programme and form | Family Planning encounters | Numerator ready; women 15 to 49 not in lake |
| RMN-15 Teenage pregnancy rate | Folder is empty | ANC enrolment plus date of birth | ANC enrolment plus birth date | EMR only; girls 10 to 19 not in lake |
| RMN-16 ANC clients aged 10 to 19 | Folder is empty | ANC enrolment plus date of birth | ANC enrolment plus birth date | EMR only, and fully computable |
| RMN-17 HPV vaccination coverage | No | HPV Vaccine form (about 470 patients, 262 facilities) | Not confirmed | Tiberbu, but volumes are very small; girls 10 to 14 not in lake |
| RMN-18 Vitamin A supplementation | No | Vitamin A Supplementation form | CWC forms | Tiberbu; children 6 to 59 months not in lake |
| RMN-19 Exclusive breastfeeding at CWC | No | Exclusive Breastfeeding Form | CWC forms | Tiberbu, from September 2025 |
| RMN-20 OTP default rate | No | No form of its own; Nutrition Services programme and form | Nutrition enrolment and discontinuation | To be checked at field level |

## What the lake cannot supply

- **Population denominators.** Expected pregnancies, expected deliveries, surviving infants, women aged 15 to 49, girls aged 10 to 19 and children aged 6 to 59 months come from KNBS projections, which are not in the lake. Seven of the 20 indicators need them.
- **The survey-based tiles on the dashboard mock-ups.** Under-5 mortality, stunting, wasting, contraceptive prevalence, unmet need, and the splits by wealth, education and urban or rural residence come from household surveys.
- **Community health data** (home visits, community referrals) from eCHIS.
- **National reach for patient-level indicators.** Tiberbu and KenyaEMR together cover about 4,300 facilities; KHIS reports from up to 7,500. An indicator built only from EMR records describes the facilities on those systems, not the country.

## Still to confirm

1. **Whether Tiberbu's forms table is complete.** It was restarted on 30 July 2026 and may be missing earlier records.
2. **Whether the two KHIS sources agree.** Compare a KHIS figure such as deliveries with the same count built from Tiberbu records for the same facilities and months.
3. **Which form fields carry each indicator**: ANC contact number, place and outcome of delivery, time of first postnatal check, chlorhexidine, vaccine doses and dates.
4. **HPV vaccination**: Tiberbu has an HPV Vaccine form with only about 470 patients, which looks far too low for routine delivery. Find out where HPV doses are really recorded (it may be school-based and reported straight to KHIS).
5. **How Tiberbu and KenyaEMR facilities map to KHIS facility IDs**, which is needed to combine the sources. Tiberbu's `company_settings` has a `dhis_id` column for this.
6. **Whether a mother is counted in more than one system**, since women can attend facilities on different systems.
