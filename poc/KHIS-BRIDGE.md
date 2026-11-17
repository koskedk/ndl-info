# KHIS interim bridge: what to pull and where to put it

This page is the brief for building the KHIS bridge. It says what to pull from the KHIS API for the RMNCAH-N indicators, and which Iceberg tables to write into the local S3 so the transform project can read them.

Everything here was checked against live KHIS on 16 November 2026. Malaria and the other programmes are left out for now.

## Why a bridge

- **The KHIS figures in DHA's lake stop at June 2026**, and they are ready-made indicators with no raw counts behind them.
- **Tiberbu can only be reported from August 2026.** So today no month has both a KHIS figure and a figure built from patient records.
- **KHIS itself has data to October 2026**, with the raw counts for all six indicators, and the population estimates the later indicators need.

The bridge is temporary. It exists until DHA stages this data in its own lake, and it should be labelled as temporary wherever it appears.

## The source

| | |
|---|---|
| System | KHIS, which is DHIS2 version 2.40 |
| Address | `HIS_KENYA_URL` in `.env` (the host is `hiskenya.dha.go.ke`); API paths below are under `/api` |
| Sign-in | Basic authentication with `HIS_KENYA_USERNAME` and `HIS_KENYA_PASSWORD` from `.env` |
| What the account can do | Read only, national view. Raw values, aggregated values and reporting rates all work |

Never write the user name or password into code, logs or this repository. Before the bridge runs on a schedule, ask DHA for a service account; the present one belongs to a person.

## What to pull

| # | What | KHIS dataset | Period | For which places |
|---|---|---|---|---|
| 1 | Monthly service counts, the whole form | MOH 711 Integrated Summary Report, Rev 2020: `UpS2bTVcClZ` | Monthly, from July 2025 | The seven facilities |
| 2 | Population estimates | Population Estimates Revised (SubCounty): `XuVxScOosIt`, and Population Estimates (Facility & Ward): `HQ6Nw1ER6Id` | Yearly, 2025 and 2026 | The seven facilities, and every sub-county of the four counties |
| 3 | Reporting rates for MOH 711 | The same dataset, through the analytics API | Monthly, from July 2025 | The seven facilities |
| 4 | Definitions | Data elements, category option combinations, datasets, organisation units | | Whatever items 1 to 3 refer to |

Things to know:

- **Pull the whole MOH 711 form, not a list of elements.** It has 253 data elements, of which the seven facilities fill 187. The six indicators use 18 of them; the rest serve the later RMNCAH-N indicators at no extra cost.
- **The volume is small.** MOH 711 for the seven facilities, July 2025 to October 2026, is 9,988 values. A full reload on every run is fine.
- **The two population datasets share most of their data elements**, so the same value comes back from both. Keep one row per data element, period, place and category option combination.
- **Population is stored for facilities and sub-counties, not for counties.** A county's figure is the sum of its sub-counties, which is why item 2 asks for every sub-county of the four counties. Wards are patchy (two of the seven wards, 2025 only), so do not rely on them.
- **Values change after they are entered.** 41 MOH 711 values for these facilities were edited in the seven days before this page was written. A full reload picks that up. If the bridge is later made incremental, use `lastUpdatedDuration` and `includeDeleted=true`.

### The places

Find them by MFL code from the Master Facility List (`transform/seeds/master_facility_list.csv`), not from a list typed into code. In KHIS the MFL code is the organisation unit's `code`:

```
GET /api/organisationUnits?filter=code:in:[15753,15209,15969,14841,14085,13738,14080]
    &fields=id,code,name,level,path,ancestors[id,name,level]&paging=false
```

The answer on 16 November 2026, for checking:

| MFL code | KHIS ID | Facility | Sub-county (ID) | County (ID) |
|---|---|---|---|---|
| 15753 | `g1sQi5lt96i` | Turbo Sub County Hospital | Turbo (`KuprsuBe1l0`) | Uasin Gishu (`pZqQRRW7PHP`) |
| 15209 | `cxqZPcA0nwV` | Moi's Bridge Health Centre | Soy (`lmr1q6dTaso`) | Uasin Gishu |
| 14841 | `SFjMLzXWaWY` | Kesses Health Centre | Kesses (`dKHnvt7gleN`) | Uasin Gishu |
| 15969 | `k0yug2XqYRT` | Lumakanda County Hospital | Lugari (`ZOdhgR19Akq`) | Kakamega (`BjC1xL40gHo`) |
| 14085 | `z4pEZ9GMUj7` | Sigomere Sub County Hospital | Ugunja (`m9nsQ1MXlVU`) | Siaya (`u4t9H8XyU9P`) |
| 14080 | `b3yukBxVi1J` | Siaya County Referral Hospital | Alego Usonga (`Cu46otDi1RO`) | Siaya |
| 13738 | `qa07L6R8UeS` | Lumumba Sub County Hospital | Kisumu Central (`OpLt8IgyHop`) | Kisumu (`tAbBVBbueqD`) |

KHIS levels are: 1 Kenya, 2 county, 3 sub-county, 4 ward, 5 health facility. Every sub-county of a county is `filter=level:eq:3&filter=path:like:<county ID>`.

### The calls

Raw values (items 1 and 2). `orgUnit` can be repeated:

```
GET /api/dataValueSets?dataSet=UpS2bTVcClZ&startDate=2025-07-01&endDate=<today>
    &orgUnit=g1sQi5lt96i&orgUnit=cxqZPcA0nwV&...
```

Each value comes back with `dataElement`, `period`, `orgUnit`, `categoryOptionCombo`, `attributeOptionCombo`, `value`, `created`, `lastUpdated`, `followup`, `storedBy` and `comment`.

Reporting rates (item 3):

```
GET /api/analytics?dimension=dx:UpS2bTVcClZ.REPORTING_RATE;UpS2bTVcClZ.REPORTING_RATE_ON_TIME;
    UpS2bTVcClZ.ACTUAL_REPORTS;UpS2bTVcClZ.ACTUAL_REPORTS_ON_TIME;UpS2bTVcClZ.EXPECTED_REPORTS
    &dimension=pe:202507;202508;...&dimension=ou:g1sQi5lt96i;cxqZPcA0nwV;...&skipMeta=true
```

Definitions (item 4):

```
GET /api/dataSets/UpS2bTVcClZ?fields=id,name,periodType,dataSetElements[dataElement[id,name,shortName,valueType,aggregationType,categoryCombo[id,name]]]
GET /api/categoryOptionCombos?fields=id,name,categoryCombo[id,name]&paging=false
```

## Where it lands

Write Iceberg tables into their own folder in the local S3, beside the folders that copy DHA's lake:

```
dha-analytics/
  iceberg/
    hmis_tiberbu_ingestion/      copied from DHA's lake
    hmis_kenya_emr_conso/        copied from DHA's lake
    hmis_ampath_prod/            copied from DHA's lake
    bridge_khis/                 written by this bridge
      data_value/
      reporting_rate/
      data_element/
      category_option_combo/
      data_set_element/
      organisation_unit/
```

Why a folder of its own, and why Iceberg:

- **Its own folder keeps the two origins apart.** Everything else under `iceberg/` is a copy of what DHA's lake holds. `bridge_khis` is data NHAI fetched itself, and the name says so wherever the table appears.
- **Iceberg means nothing new is needed to read it.** The transform project lists a table by adding one line to `ops/bronze-tables.csv`. Plain Parquet files would need a second kind of catalog in Trino.
- **It can be removed cleanly** when DHA stages KHIS in its own lake: delete the folder and repoint the staging models.

### The tables

One row per item named in bold. Column names are lower case with underscores.

| Table | One row is | Columns |
|---|---|---|
| `data_value` | **One reported value**: a data element, for a period, at a place, for one category option combination | `data_element_id`, `period` (as KHIS writes it: `202610` or `2026`), `organisation_unit_id`, `category_option_combo_id`, `attribute_option_combo_id`, `value` (text, as received), `created_at`, `last_updated_at`, `follow_up`, `loaded_at` |
| `reporting_rate` | **One dataset, period and place** | `data_set_id`, `period`, `organisation_unit_id`, `expected_reports`, `actual_reports`, `actual_reports_on_time`, `reporting_rate`, `reporting_rate_on_time`, `loaded_at` |
| `data_element` | **One data element** | `data_element_id`, `name`, `short_name`, `value_type`, `aggregation_type`, `category_combo_id`, `category_combo_name`, `loaded_at` |
| `category_option_combo` | **One category option combination** (for example "New clients" or "default") | `category_option_combo_id`, `name`, `category_combo_id`, `category_combo_name`, `loaded_at` |
| `data_set_element` | **One data element on one dataset's form** | `data_set_id`, `data_set_name`, `period_type`, `data_element_id`, `loaded_at` |
| `organisation_unit` | **One place**: each facility, and each ward, sub-county and county above it | `organisation_unit_id`, `mfl_code` (KHIS `code`), `name`, `level`, `path`, `ward_id`, `sub_county_id`, `county_id`, `loaded_at` |

Rules for the tables:

- **Leave out `storedBy` and `comment`.** The first is a person's user name and the second is free text. Neither is needed.
- **Keep `value` as text.** Every MOH 711 value pulled so far is a number, but other forms hold text and yes or no answers. Staging casts it.
- **`data_value` has one row per key.** The key is data element, period, organisation unit, category option combination and attribute option combination.
- **All three datasets go into the one `data_value` table.** Monthly counts and yearly population differ only in the period. `data_set_element` says which form an element belongs to.
- **`loaded_at` is the time the bridge ran**, the same on every row of a run.
- **Do not unpack the category option combinations into columns.** MOH 711 uses 19 of them; most elements use only "default". Staging joins to `category_option_combo` when it needs the split.

### Writing them

The local S3 has no Iceberg catalog. A table is a folder with `data/` and `metadata/`, and readers take the newest `metadata/NNNNN-*.metadata.json`. The copies of DHA's lake are written that way, with pyiceberg and a throwaway catalog:

```python
catalog = SqlCatalog("bridge", uri="sqlite:///:memory:", warehouse=f"s3://{bucket}", **s3_properties)
catalog.create_namespace("bridge_khis")
table = catalog.create_table("bridge_khis.data_value", schema=schema,
                             location=f"s3://{bucket}/iceberg/bridge_khis/data_value")
table.append(rows)          # a pyarrow table
```

- **Empty the table's folder before a full reload**, so the folder holds one table and not the remains of the last one.
- **The plan names dlt for interim bridges.** If dlt is used, check that it leaves the metadata files in that place. If it does not, let dlt fetch and write Parquet, and load that with the few lines above.
- **Write with the stand-in's write key** (`STANDIN_S3_WRITE_ACCESS_KEY` and `STANDIN_S3_WRITE_SECRET_KEY` in `.env`). The ordinary key can only read.

## What the indicators will read

This is for checking a load, and it becomes a managed list in the transform project. All are MOH 711 data elements.

| Indicator | Numerator | Denominator |
|---|---|---|
| RMN-16 ANC clients aged 10 to 19 | Adolescents presenting with pregnancy at first ANC visit: 10 to 14 years `chMsCa5zcn7`, 15 to 19 years `uHBmKxktYk0` | New ANC clients `f9vesk5d4IY` |
| RMN-04 Postnatal care, mother, within 48 hours | Mothers receiving postpartum care within 48 hours `qahRo2120r8` | Deliveries: normal `jaPrPmor6WV`, caesarean `rAZBTMa7Jy3`, breech `sMqM8DwiAaj`, assisted vaginal `Kx64gGqaFVq` |
| RMN-08 Postnatal care, newborn, within 48 hours | Infants receiving postpartum care within 48 hours `wxg6cuH9cXF` | Live births `UqKC1DJnymn` |
| RMN-06 Facility neonatal mortality | Neonatal deaths 0 to 28 days `GAr6xu6f1n7` | Live births `UqKC1DJnymn` |
| RMN-01 Facility maternal mortality | Maternal deaths: 10 to 14 `KDFtI6rqYwI`, 15 to 19 `BYMSIbnUzXQ`, 20 to 24 `AC1Iorxdijc`, 25 and over `dPRCstLVkZu` | Deliveries, as for RMN-04 |
| RMN-05 Maternal death audit completion | Maternal deaths audited within 7 days `kAp7ViUXEKh` | Maternal deaths, as for RMN-01 |

- **Do not add "Maternal Deaths 20+ years" (`eBHhfupqMHz`) to the four age bands.** It is an older element still on the form and would count deaths twice.
- **Audits can exceed deaths in a period.** A death in one month can be audited in the next.

Elements for later indicators, already on the same form: eighth ANC contact `cKr5133RFuN`, fresh stillbirth `rYn8RCcHJg1`, chlorhexidine for cord care `bPpRMDzpXXN`, neonatal deaths audited within 7 days `tHRlLvvCObn`, low birth weight `syjjPqXbjTm`.

Population elements the later indicators need:

| Estimate | Data element | Stored for |
|---|---|---|
| Total population | `NLKRV7bYbVy` | Facility, sub-county |
| Estimated number of pregnant women | `pct05jgGcLt` | Facility, sub-county |
| Estimated deliveries | `tmlMpIqHimf` | Facility, sub-county |
| Estimated live births | `JOnT3OiMd5o` | Facility, sub-county |
| Surviving infants (under 1 year) | `pMbuvKvH4rg` | Facility, sub-county |
| Women of childbearing age (15 to 49) | `bPQDV3mud0v` | Facility, sub-county |
| Girls aged 10 to 14 | `dRhugDCanvB` | Sub-county only |
| Population 6 to 59 months | `pkgghI15gSL` | Facility, sub-county |

KHIS carries these estimates; KNBS produces them. Say so in the bridge's description.

## Checking a load

Figures from KHIS on 16 November 2026. Later loads will be a little higher, because facilities keep reporting and correcting.

- **MOH 711:** 9,988 values for the seven facilities, periods `202507` to `202610`, 187 data elements, 19 category option combinations, one attribute option combination.
- **Every facility has values in at least 15 of the 16 months.**
- **Population:** each of the seven facilities and each of their seven sub-counties has values for both 2025 and 2026. No county has a stored value.
- **Reporting rates:** five figures per facility per month.
- **Totals across the seven facilities, August to October 2026:**

| Element | Total |
|---|---:|
| New ANC clients | 1,298 |
| Adolescents at first ANC, 10 to 14 and 15 to 19 | 3 and 135 |
| Mothers receiving postpartum care within 48 hours | 1,126 |
| Infants receiving postpartum care within 48 hours | 1,162 |
| Live births | 1,590 |
| Deliveries (normal, caesarean, breech, assisted) | 1,649, 184, 8, 1 |
| Neonatal deaths 0 to 28 days | 11 |
| Maternal deaths, all four age bands | 3 |
| Maternal deaths audited within 7 days | 4 |

## After the tables are written

1. In `ndl-poc-transform`, add a line per table to `ops/bronze-tables.csv` (`bridge_khis,bridge_khis,data_value` and so on) and to `dbt/models/sources.yml`, then run `make bronze`.
2. In this project, add `bridge_khis,bridge_khis,KHIS (interim bridge)` to `source-sample/source-folders.csv`, so `make tables` names the folder.
3. `make export-source` carries the new tables to teammates with everything else.

## Not covered here

- **Malaria**, and the other programmes. Their forms (outpatient, laboratory and inpatient summaries) come later.
- **Other RMNCAH-N forms.** Immunisation is on MOH 710 Rev 2020 (`XoHnrLBL1qB`) and nutrition on MOH 713 (`DWKwKC6dnoB`). Causes of maternal and perinatal death are on the Maternal Death Summary Form (`m6EF2FDkLAE`), which is reported daily by about 600 facilities.
- **Death cases and their reviews.** MPDSR is on the KHIS tracker, a separate DHIS2 from KHIS. Its bridge has its own brief: [MPDSR-TRACKER-BRIDGE.md](MPDSR-TRACKER-BRIDGE.md). The MOH 711 death totals pulled here stay, as the figures to check it against.
- **County boundaries.** KHIS holds a shape for each county, which the boundaries bridge can use.
- **More facilities.** Widening from seven facilities to every facility in the four counties changes the list of places and nothing else.
