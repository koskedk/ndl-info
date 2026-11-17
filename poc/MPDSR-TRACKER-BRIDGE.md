# KHIS tracker interim bridge: death cases from MPDSR

This page is the brief for building the tracker bridge. It says what to pull from the KHIS tracker for maternal, neonatal and perinatal deaths, and which Iceberg tables to write into the local S3 so the transform project can read them. It follows the same headings as the [KHIS bridge brief](KHIS-BRIDGE.md), and reuses its choices wherever it can.

The tracker's set-up was read on 17 November 2026: the forms, their fields and the number of records. **No record's answers were read**, so anything about how the fields are filled in is marked **not checked**.

**What to stage follows the analysts' own pipeline.** DHA's analysts already pull these forms into SQL Server with two scripts of the KHIS MNH project, `mpdsr.py` and `pdsr.py`. This bridge stages the same forms and the same fields in tables of the same shape, so their queries can be carried over. Where it differs, and why, is under ["How this differs from the analysts' pipeline"](#how-this-differs-from-the-analysts-pipeline).

## Why a bridge

- **Tiberbu has too few death records to report from.** Bronze holds 2 maternal death notices, and no maternal notice is marked as audited anywhere in Tiberbu in 2026.
- **KHIS gives monthly totals only.** MOH 711 has the number of deaths and audits per facility and month, with no record behind them: no cause, no age at death, no review date.
- **The tracker holds one record per death, and one per review.** MPDSR (maternal and perinatal death surveillance and response) is on it in full. That is what the three death indicators need: RMN-01 (facility maternal mortality), RMN-06 (facility neonatal mortality) and RMN-05 (maternal death audit completion). Perinatal deaths and stillbirths come from the same forms, for the later indicators.

The bridge is temporary, as the KHIS one is. It exists until DHA stages this data in its own lake, and it should be labelled as temporary wherever it appears.

## The source

| | |
|---|---|
| System | The KHIS tracker, which is DHIS2 version 2.36.13. It is a separate system from KHIS (DHIS2 2.40), so some API calls differ |
| Address | `HIS_TRACKER_URL` in `.env` (the host is `histracker.dha.go.ke`); API paths below are under `/api` |
| Sign-in | Basic authentication with `HIS_TRACKER_USERNAME` and `HIS_TRACKER_PASSWORD` from `.env` |
| What the account can do | National view. **It can write as well as read** in every form listed below |

Three things to know before writing any code:

- **The account can change data, so the bridge must only ever send GET requests.** Nothing in the bridge may post, put or delete. Before it runs on a schedule, ask DHA for a read-only service account; the present one belongs to a person.
- **The server refuses Python's own web client.** Cloudflare, which sits in front of the tracker, answers it with "403, error 1010: access denied based on your browser's signature", before the sign-in is looked at. `curl` is accepted. The structure script calls `curl`; the bridge can do the same. KHIS gave the same client a 403 on the same day, and the reason there was not read.
- **Never write the user name or password into code, logs or this repository.** With `curl`, pass the sign-in on standard input (`--config -`), not on the command line, where other programs on the machine can see it.

**The structure script.** `source-sample/checks/tracker_mpdsr_structure.py` read everything on this page. It reads definitions and totals only, and every call is a GET. It is not part of the shared copy; the project lead runs it when the forms change and updates this page.

## What to pull

Eight forms. Each is a DHIS2 **event programme with one stage**: one filled-in form is one event. There are no tracked entities and no enrolments.

| Key | Form | Programme ID | Stage ID | Fields | Records, all facilities | In the analysts' pipeline |
|---|---|---|---|---:|---:|---|
| `MDN_2025` | Maternal Death Notification Form Rev 2025 | `orgIzwnrwEG` | `NnIxZdXv4MH` | 35 | 827 | `mpdsr.py` |
| `MDR` | Maternal Death Review Form Rev 2025 | `m6U01IixAdW` | `I6a6GPijAci` | 211 | 757 | `mpdsr.py` |
| `C_MDN` | Community Maternal Death Notification (C-MDN) Form | `gsV6ZGGQSqK` | `qUBD0Wa5x0Z` | 19 | 24 | `mpdsr.py` |
| `C_MD_VA` | Community Maternal Death VA (verbal autopsy) | `IOaRQKgCrPO` | `IPfyEeicVGF` | 25 | 0 | `mpdsr.py` |
| `PDN` | Perinatal Death Notification Form Rev 2025 | `TcVXzAKCVdU` | `CKb1sJpJdIh` | 41 | 5,750 | `pdsr.py` |
| `PDR` | Perinatal Death Review Form Rev 2025 | `qjk3GCpkIoa` | `b7L9XmsLpIC` | 191 | 4,450 | `pdsr.py` |
| `NDN` | Neonatal Death Notification Form REV 2025 | `z9p4TifTD9m` | `WVVxHjIdNgr` | 45 | 1,380 | Not there. Added here |
| `NDR` | Neonatal Death Review Form Rev 2025 | `YwtPT5i5ccz` | `LXMFR3eapmv` | 655 | 765 | Not there. Added here |

The key is the analysts' short name for the form, kept as the `program_key` column. `NDN` and `NDR` are ours, in the same style.

Pull, for the seven facilities:

1. **Every event of the eight forms.**
2. **Every answer on it**, as the analysts' pipeline does. Nothing is left out in bronze; see "Personal data" for what that means downstream.
3. **The dictionary**: every field on each form, and every choice in each list of options.
4. **The places**: the organisation units.

Things to know:

- **The two neonatal forms are not in the analysts' pipeline, and are needed.** Late neonatal deaths are recorded only there, so the neonatal mortality indicator cannot be built without them.
- **Early neonatal deaths are on the perinatal form, not the neonatal one.** The perinatal form's period of death is antepartum, intrapartum, early neonatal or unknown. The neonatal form's is late neonatal or unknown. So a count of neonatal deaths needs both forms.
- **Stillbirths are on the perinatal form**: the baby's outcome is live birth, fresh stillbirth or macerated stillbirth.
- **A notification and its review are two events in two forms.** Three fields are on the six facility forms and tie them together: `MPDSR Case ID` (`AvLykgDSa8f`), `MPDSR Review Status` (`cx4xSt3r9hN`, yes or no) and `MPDSR Review Event ID` (`vobAuF9as7h`). How they are filled in is **not checked**.
- **The numbers are small.** The seven facilities have 28 notifications and 8 reviews in all, and nothing on the two community forms. A full reload on every run is fine.
- **Three of the seven facilities have no record at all**: Kesses, Moi's Bridge and Sigomere.
- **The first records at the seven facilities are from April 2026.** Pull every event, with no start date, as the analysts' pipeline does.
- **An event's date is not the date of death.** Each form has its own date of death field. Staging uses that.

### The places

Find them by MFL code from the Master Facility List (`transform/seeds/master_facility_list.csv`), exactly as the KHIS bridge does:

```
GET /api/organisationUnits?filter=code:in:[15753,15209,15969,14841,14085,13738,14080]
    &fields=id,code,name,level,path,ancestors[id,name,level]&paging=false
```

All seven are found, at level 5, and **each has the same ID as in KHIS** (the table is in the [KHIS brief](KHIS-BRIDGE.md#the-places)). Look them up all the same, so the bridge does not depend on that staying true.

### The calls

Events and their answers, one facility and one form at a time. The analysts' pipeline makes the same call for all facilities at once (`ouMode=ACCESSIBLE`, no `orgUnit`):

```
GET /api/tracker/events?program=<programme ID>&orgUnit=<facility ID>&ouMode=SELECTED
    &fields=event,program,programStage,orgUnit,orgUnitName,enrollment,trackedEntity,status,occurredAt,
            completedAt,createdAt,updatedAt,storedBy,deleted,dataValues[dataElement,value]
    &page=1&pageSize=500
```

- **The rows come back under `instances`**, not `events`, in this version.
- **Read page after page** until a page has fewer rows than `pageSize`. To get a count without the rows, add `totalPages=true&pageSize=1` and read `total`.
- **Checked here**: the call without `dataValues`, `orgUnitName`, `storedBy` and `deleted`. The fuller field list is the analysts'; this project has not run it.
- **If `/api/tracker/events` does not answer**, the analysts' pipeline falls back to the older call: `GET /api/events?program=...&ouMode=...&fields=event,program,programStage,orgUnit,orgUnitName,status,eventDate,created,lastUpdated,storedBy,dataValues[dataElement,value]&skipMeta=true`.

The dictionary, one form at a time, exactly as the analysts' pipeline asks for it:

```
GET /api/programs/<programme ID>?fields=id,name,programType,programStages[id,name,programStageDataElements[
    sortOrder,compulsory,dataElement[id,name,shortName,formName,valueType,optionSet[id,options[code,name]]]]]
```

## Where it lands

A folder of its own, beside `bridge_khis`:

```
dha-analytics/
  iceberg/
    bridge_khis/                 written by the KHIS bridge
    bridge_khis_tracker/         written by this bridge
      event/
      event_data_value/
      data_element/
      option/
      organisation_unit/
```

The reasons are the same as for `bridge_khis`: its own folder keeps what NHAI fetched apart from the copies of DHA's lake, Iceberg means the transform project reads it with one line per table, and the folder can be removed cleanly when DHA stages the tracker itself.

### The tables

The first four tables are the analysts' tables. Theirs come in two sets, `mpdsr_...` and `pdsr_...`; here each pair is one table, told apart by `program_key`. Column names follow this project's style, with the analysts' name beside each where it differs.

| Table | Analysts' tables | One row is | Columns (analysts' name) |
|---|---|---|---|
| `event` | `mpdsr_events`, `pdsr_events` | **One filled-in form**: a notification, a review or a verbal autopsy | `event_id`, `program_key`, `program_id` (`program_uid`), `program_stage_id` (`program_stage_uid`), `organisation_unit_id` (`ou_id`), `organisation_unit_name` (`ou_name`), `enrollment_id` (`enrollment_uid`), `tracked_entity_id` (`tracked_entity_uid`), `status` (`event_status`), `event_date`, `created_at`, `updated_at`, `stored_by`, `completed_at`, `deleted`, `loaded_at` (`load_ts`) |
| `event_data_value` | `mpdsr_event_values`, `pdsr_event_values` | **One answer on one form** | `event_id`, `program_key`, `data_element_id` (`data_element_uid`), `value` (`value_raw`), `value_label` |
| `data_element` | `mpdsr_data_elements`, `pdsr_data_elements` | **One field on one form** | `program_key`, `program_id` (`program_uid`), `program_stage_id` (`program_stage_uid`), `program_stage_name`, `data_element_id` (`data_element_uid`), `name` (`de_name`), `form_name` (`de_form_name`), `value_type`, `sort_order`, `compulsory`, `has_options`, `restricted`, `loaded_at` |
| `option` | `mpdsr_element_options`, `pdsr_element_options` | **One choice of one field** | `data_element_id` (`data_element_uid`), `code` (`option_code`), `name` (`option_name`), `loaded_at` |
| `organisation_unit` | none | **One place**: each facility, and each ward, sub-county and county above it | The same columns as in `bridge_khis` |

Rules for the tables:

- **Keep answers long, one row per answer**, as the analysts do. The neonatal review form alone has 655 fields, and a new field then never breaks the load.
- **`value` is the answer as the tracker holds it, as text.** For a field with a list of options it is the option's code.
- **`value_label` is that code's name**, looked up in the form's own list. It is empty for a field with no list.
- **`form_name` is the field's wording on the form**: DHIS2's `formName`, or else its `shortName`, or else its `name`.
- **`event_date` is the date part of the event's `occurredAt`.**
- **`enrollment_id` and `tracked_entity_id` are always empty** for these forms. They are kept so the table matches the analysts'.
- **`restricted` is true for a field on the restricted list**; see "Personal data". `completed_at`, `deleted` and `restricted` are this project's additions.
- **`loaded_at` is the time the bridge ran**, the same on every row of a run.
- **`organisation_unit` has the same shape as the KHIS one**, so one staging model can serve both.

### Personal data

**Bronze holds every field, as the analysts' tables do.** That was decided on 17 November 2026, so that bronze is a faithful copy of the source. The care is taken one step later, in the transform project.

What the forms hold:

- **They do not name the person who died.** No field asks for the name or the national ID of the mother or the baby.
- **About the health worker who filled in the form**: name, designation or cadre, telephone, e-mail and, on one form, signature. `stored_by` on the event is the user name of whoever entered it.
- **Record numbers and addresses**: the neonatal review's inpatient number (`MPDSR_NDR_IPNumber`), the perinatal review's serial number and village or estate, and the community notification's household number.
- **A great deal of typed text**, including review findings.

The rules:

- **`source-sample/tracker-fields-restricted.csv` lists the fields that must never reach silver or gold.** It has 447 fields across the eight forms: every telephone and e-mail field, and every typed-text field with no list of options. The bridge copies it into `data_element.restricted`.
- **The list is made by rule, by the structure script, and it errs on the side of restricting.** It catches harmless typed fields too, such as the county's name and the time of death. A field comes off the list on purpose, after looking at what it holds.
- **`stored_by` is restricted as well**, though it is a column and not a field on the list.
- **In the transform project, a staging model names the fields it reads.** It never selects all answers, and `make scan` is run after each new silver or gold table.
- **A death at a named facility in a named month can point to a family**, even without a name. These tables stay in the proof of concept's S3 and its encrypted exports, and go no further.
- **Leave out coordinates and geometry.** The analysts' pipeline does not pull them either.

### Writing them

Write them exactly as the KHIS bridge writes its tables: pyiceberg with a throwaway catalog, the table's folder emptied before a full reload, and the stand-in's write key. See ["Writing them" in the KHIS brief](KHIS-BRIDGE.md#writing-them); only the namespace changes, to `bridge_khis_tracker`.

### How this differs from the analysts' pipeline

| | The analysts' pipeline | This bridge | Why |
|---|---|---|---|
| Forms | Six: maternal and perinatal notification and review, and the two community maternal forms | The same six, and the two neonatal forms | Late neonatal deaths are only on the neonatal forms |
| Fields | Every field | Every field | The same |
| Places | Every facility the account can see | The seven facilities on the Master Facility List | The rest of the proof of concept covers those seven. Widening is one setting: `ouMode=ACCESSIBLE` |
| Lands in | SQL Server, tables `mpdsr_...` and `pdsr_...` | Iceberg in the local S3, one set of tables with `program_key` | The transform project reads bronze through Trino |
| Loading | First run in full, then events changed since the last run, less 30 days | In full on every run | 36 records. A full reload also drops events deleted on the tracker, which a changes-only load keeps |
| Run log | `mpdsr_pull_log`, `pdsr_pull_log` | None; `loaded_at` on every row | Nothing to resume from in a full reload |
| Client | Python `requests` | `curl` | Cloudflare refused Python's built-in client here. Whether it accepts `requests` was not tried |
| Sign-in | Basic authentication, then a form log-in if that fails | Basic authentication only | A form log-in is a POST, and this bridge sends only GET requests |

## What the indicators will read

This is for checking a load, and it becomes a managed list in the transform project. The place of every death is the event's organisation unit.

**Maternal deaths (RMN-01), from the maternal notification form:**

| What | Field | ID |
|---|---|---|
| Date of death (required) | `MPDSR_MDN_17_Date_of_death` | `ePobV76ZAa7` |
| Date of notification (required) | `MPDSR_MDN_1_Date_of_notification` | `dh8BmHfRJrq` |
| The woman's age in years (required) | `MPDSR_MDN_6_Age_in_years` | `dJIqBdee7vD` |
| Underlying cause, from a list | `MPDSR_MDN_22_Underlying_cause_of_death_direct` | `Nyos5CKFkA7` |
| Referred from another facility | `MPDSR_MDN_20_Referral_from_another_facility` | `M9gtNuWOOLX` |

**Maternal death reviews (RMN-05):**

| What | Form | Field | ID |
|---|---|---|---|
| Whether the death was reviewed | Notification | `MPDSR Review Status` | `cx4xSt3r9hN` |
| Which review it was | Notification | `MPDSR Review Event ID` | `vobAuF9as7h` |
| Date of the review | Review | `MPDSR_MDR_4_Date_of_audit_review` | `nX1iaZgq7P0` |
| Date of death, as the review has it | Review | `MPDSR_MDR_21_Date_of_death` | `NVBCZgN9CCz` |

**Neonatal deaths (RMN-06), from two forms:**

| What | Neonatal notification | Perinatal notification |
|---|---|---|
| Date of death (required) | `MPDSR_NDN_DateOfDeath` `qS3ccqdHT50` | `MPDSR_PDN_5_DateOfDeath` `HFi3lnwbz7E` |
| Date of birth (required) | `MPDSR_NDN_DateOfBirth` `tnsvAn8A7IN` | `MPDSR_PDN_7_DateOfBirth` `p7oIgPdQqks` |
| Age at death in days | `MPDSR_NDN_AgeAtDeathDays` `e0M4hWIU8C3` | `MPDSR_PDN_17_AgeAtTimeOfDeath_Days` `Ck8VpvVwlkk` |
| Period of death | `MPDSR_NDN_PeriodOfDeath` `xdgwwU6D73n` | `MPDSR_PDN_29_PeriodOfDeath` `fRCAW8sS34A` |
| Baby's outcome (live birth or stillbirth) | not on this form | `MPDSR_PDN_10_BabyOutcome` `ZpYMHGGjXgr` |
| Birth weight in grams | `MPDSR_NDN_BirthWeight_g` `SBt5pl3JExR` | `MPDSR_PDN_11_BirthWeight` `JccRoxT3Pkt` |
| Cause, from a list | `MPDSR_NDN_NeonatalCause_Broad` `ZdFumiRfrWU` | `MPDSR_PDN_30_Perinatal_Cause_of_death` `eXyExtMXiEh` |
| Place of birth | `MPDSR_NDN_PlaceOfChildbirth` `tbwNURtInH9` | `MPDSR_PDN_26_PlaceOfChildbirth` `unrQ5mACX25` |
| Mother's age | `MPDSR_NDN_Mother_Age` `oeg1jU1CKMl` | `MPDSR_PDN_18_MothersAge` `hlGwY5OdVZq` |

The review dates for the later audit indicators are `MPDSR_NDR_DateOfAudit` (`Ba4b3oV5bKu`) and `MPDSR_PDR_DateOfAudit` (`S4nrnLJ4R17`).

Not checked, because no answers were read:

- **Whether `MPDSR Review Status` is kept up to date**, or whether a review has to be found through the case ID.
- **Whether a perinatal notification with a live birth always has "early neonatal" as its period of death.**
- **How often the fields that are not required are filled in.**

## Checking a load

Records at the seven facilities on 17 November 2026, by the event's date. Later loads will be a little higher.

| Facility | Maternal notification | Maternal review | Neonatal notification | Neonatal review | Perinatal notification | Perinatal review |
|---|---:|---:|---:|---:|---:|---:|
| Lumumba Sub County Hospital | 1 | 1 | 1 | 0 | 6 | 6 |
| Siaya County Referral Hospital | 5 | 0 | 0 | 0 | 0 | 0 |
| Turbo Sub County Hospital | 4 | 0 | 4 | 0 | 5 | 0 |
| Lumakanda County Hospital | 1 | 1 | 1 | 0 | 0 | 0 |
| Kesses, Moi's Bridge, Sigomere | 0 | 0 | 0 | 0 | 0 | 0 |
| **All seven** | **11** | **2** | **6** | **0** | **11** | **6** |

The two community maternal forms have no record at the seven facilities.

Beside KHIS's own monthly totals for the seven facilities, August to October 2026:

| | MOH 711 | The tracker, by event date |
|---|---:|---|
| Maternal deaths | 3 | 4 notifications |
| Maternal deaths audited within 7 days | 4 | 2 reviews |
| Neonatal deaths 0 to 28 days | 11 | 4 neonatal notifications, and 8 perinatal ones, some of which are stillbirths |

The two are filled in by different people at different times, and the tracker's months here are event dates, not dates of death. So they are not expected to match exactly. A large gap in either direction is a finding to report, not an error in the bridge.

## After the tables are written

1. In `ndl-poc-transform`, add a line per table to `ops/bronze-tables.csv` (`khis_tracker,bridge_khis_tracker,event` and so on) and to `dbt/models/sources.yml`, then run `make bronze`.
2. In this project, add `khis_tracker,bridge_khis_tracker,KHIS tracker (interim bridge)` to `source-sample/source-folders.csv`, so `make tables` names the folder.
3. `make export-source` carries the new tables to teammates with everything else.

## Not covered here

- **Community forms for neonatal and perinatal deaths**, and their verbal autopsy forms. The analysts' pipeline lists the perinatal ones but has them switched off.
- **The MPDSR County Action Tracker Tool**, which follows up what a review recommended.
- **Older forms.** The Perinatal Death Review Form Revised 2019 is still there; the analysts' pipeline has it switched off, and this account cannot read it.
- **The other 70 or so forms on the tracker.**
- **More facilities.** Widening from seven facilities changes one setting and nothing else.
