# Malaria priority indicators: which ones bronze can answer

This page is for the team meeting that decides which malaria indicators the proof of concept builds first. It takes the 16 priority indicators of the malaria programme's guide and says, for each, whether the data now in bronze can answer it.

**The decision asked for:** agree the first group to build, agree two counting rules, and agree which missing data to ask for. The three are set out under ["What the team needs to agree"](#what-the-team-needs-to-agree).

**What has been checked.** Each indicator was checked against bronze on 19 November 2026, by counting. Only totals were produced: no individual record was viewed or saved. **Nothing has been built yet**, so each verdict says the data is there, not that a figure has been produced.

- **The guide** is `resources/Malaria_Indicators.xlsx`: one sheet, 16 indicators, all marked high priority. The guide does not number them. The numbers 1 to 16 on this page follow its order.
- **Bronze** is the copy of the lake that the proof of concept reads. It is much narrower than the whole lake described in [03-malaria-data-map.md](03-malaria-data-map.md) and [05-malaria-volumes.md](05-malaria-volumes.md): see ["What bronze holds"](#what-bronze-holds).

## The answer in short

| Verdict | How many | Which |
|---|---:|---|
| **Yes**: can be built now | 8 | 2, 5, 6, 8, 9, 10, 11, 12 |
| **Partly**: something is missing | 7 | 1, 3, 4, 7, 13, 14, 15 |
| **No** | 1 | 16 |

**Recommendation: build the eight "yes" indicators first.** They rest on records that are already in bronze and already clean, and they need no data from outside. Five start from malaria test results and three from the prevention forms.

**One limit applies to all of them: coverage.** The figures would cover Kakamega's 196 Tiberbu facilities from August 2026, and three KenyaEMR facilities in Siaya and Kisumu. They would not be national figures.

## The 16 indicators, one by one

| # | Indicator | Verdict | From | What limits it |
|---:|---|---|---|---|
| 1 | Confirmed malaria cases per 1,000 population | Partly | Tiberbu, KenyaEMR | The cases are there. Population is in bronze only for 7 facilities and their sub-counties |
| 2 | Total confirmed malaria cases | **Yes** | Tiberbu, KenyaEMR | Facility cases only. No community cases |
| 3 | Malaria inpatient cases per 10,000 population | Partly | Tiberbu, KenyaEMR | The count is there: about 900 to 1,300 admissions in Tiberbu and 254 in KenyaEMR. The same population gap |
| 4 | Malaria deaths per 100,000 population | Partly | Tiberbu | Very few deaths on record: 7 inpatient deaths with a malaria diagnosis, and 25 death notices naming malaria. The same population gap |
| 5 | Confirmed cases who received ACT | **Yes** | Tiberbu, KenyaEMR | None found. Tiberbu has about 16,500 orders for artemether/lumefantrine and 10,000 dispensed, each tied to a patient |
| 6 | Pregnant women with three or more doses of IPTp | **Yes** | Tiberbu, KenyaEMR, KHIS | Over first ANC attendance. Over estimated pregnancies, only for the 7 KHIS facilities |
| 7 | Suspected malaria cases tested | Partly | Tiberbu, KenyaEMR | No source records "suspected" in a usable way. It needs an agreed rule |
| 8 | ANC1 clients issued an ITN | **Yes** | Tiberbu, KHIS, AMRS | Not found in KenyaEMR |
| 9 | Infants issued an ITN at CWC, over infants receiving MR1 | **Yes** | Tiberbu | KHIS has the nets but not the measles-rubella doses |
| 10 | Malaria test positivity rate | **Yes** | Tiberbu, KenyaEMR | None found |
| 11 | Confirmed malaria as a share of outpatient attendance | **Yes** | Tiberbu, KenyaEMR | None found |
| 12 | Blood slide positivity rate | **Yes** | Tiberbu, KenyaEMR | None found |
| 13 | Public facilities with no stock-out of key malaria commodities | Partly | Tiberbu | Stock records cover artemether/lumefantrine at about 109 facilities and artesunate at 76. Nothing usable for SP, nets or test kits |
| 14 | Malaria case fatality rate | Partly | Tiberbu, KenyaEMR | It can be worked out, but on a handful of deaths |
| 15 | Admitting facilities reporting inpatient data | Partly | Tiberbu, KenyaEMR | The numerator is there: 60 and 3 facilities. The list of facilities that admit is not in bronze |
| 16 | Children under 5 who received all courses of SMC | No | | It comes from eCHIS in Turkana, which is not in bronze. The guide leaves its numerator and denominator blank |

## The eight to build first

**They share four kinds of record**, so the work overlaps:

| Kind of record | Indicators that use it |
|---|---|
| Malaria test results | 2, 5, 10, 11, 12 |
| Antimalarial orders and dispensing | 5 |
| Outpatient visits | 11 |
| Prevention forms: IPTp doses, nets issued, measles doses | 6, 8, 9 |

**A suggested order:**

1. **Testing: 10, 12 and 2.** Test positivity, slide positivity and confirmed cases all come from the test results alone.
2. **Cases in context: 11 and 5.** These add outpatient visits and antimalarial treatment to the confirmed cases.
3. **Prevention: 6, 8 and 9.** IPTp, nets at ANC and nets to infants come from the forms, and from MOH 711 where KHIS has it.

**They would be built like the RMNCAH-N indicators**: one row per facility, month and source system, holding counts. Sources are never added together; which source to show is chosen where the figure is shown.

## The seven that are partly answerable

| # | Indicator | What can be shown now | What would complete it |
|---:|---|---|---|
| 1 | Confirmed cases per 1,000 | The count, which is indicator 2 | County and sub-county populations |
| 3 | Inpatient cases per 10,000 | The count of admissions | The same populations |
| 4 | Deaths per 100,000 | The count of deaths | The same populations. The count itself is very small |
| 7 | Suspected cases tested | A figure under an agreed rule for "suspected" | The programme's agreement to the rule, or KHIS MOH 705 |
| 13 | No stock-out of key commodities | Stock-outs of two of the five commodities | Commodity data (LMIS) for SP, nets and test kits |
| 14 | Case fatality rate | Counts of deaths and admissions | More facilities and months. A rate on so few deaths will swing widely |
| 15 | Admitting facilities reporting | The number of facilities sending inpatient data | The list of facilities that offer admission |

## What bronze holds

- **Tiberbu is the main source.** Bronze has it for Kakamega only: 196 facilities, usable from August 2026. It holds about 67,000 malaria tests, 116,000 malaria diagnoses and 813,000 outpatient visits.
- **Its test results are clean.** Each rapid test and blood slide result is marked positive or negative, so positivity and confirmed cases need no guessing.
- **Its prevention forms are there.** They record IPTp doses by number, nets issued to women and to infants, and measles doses.
- **KenyaEMR has the same kinds of record for 3 facilities** in Siaya and Kisumu: about 23,000 test results, 9,000 malaria diagnoses and 3,000 antimalarial orders.
- **AMRS adds almost nothing**: a few hundred tests, and nets issued at ANC.
- **KHIS has only MOH 711, for 7 facilities.** That gives IPTp doses, nets to ANC clients and to infants, and new ANC clients, with population estimates for those facilities and their sub-counties.

## What is missing from bronze

| Missing | What it would add |
|---|---|
| KHIS outpatient forms (MOH 705A and B) | A KHIS figure beside the EMR one for indicators 1, 2, 7, 10 and 11, and national reach |
| KHIS laboratory form (MOH 706) | The same for indicators 10 and 12 |
| KHIS immunisation form (MOH 710) | Measles-rubella doses, the denominator of indicator 9 |
| KHIS inpatient forms | Admissions and deaths for indicators 3, 4, 14 and 15 |
| County and sub-county populations | The denominators of indicators 1, 3 and 4 |
| The list of facilities that admit | The denominator of indicator 15 |
| Commodity data (LMIS) | Indicator 13 in full |
| Community data (eCHIS) | Community cases for indicators 1, 2, 5, 7 and 10, and indicator 16 |

## What the team needs to agree

1. **Which indicators to proceed on.** The recommendation is the eight marked "yes", in the order above. Say if any of the seven "partly" should come forward as counts, for example inpatient cases (3).

2. **What counts as a confirmed case.** The recommendation is a positive rapid test or blood slide, as the guide says ("confirmed by microscopy or mRDT"). The diagnosis text is not used for this: Tiberbu's labels "Confirmed malaria" and "Suspected Malaria" contradict its own flag.

3. **What counts as a suspected case (indicator 7).** Tiberbu marks 80% of all its diagnoses as suspected, whatever the disease, so that flag cannot be used. The proposal is: a suspected case is any visit with a malaria test or a malaria diagnosis, and a tested one is any of those with a test. **This needs the programme's word** before indicator 7 is built.

4. **Which denominator for IPTp and nets at ANC (6 and 8).** The guide names two: estimated pregnant women, and first ANC attendance. The recommendation is first ANC attendance for now, since estimated pregnancies exist only for 7 facilities.

5. **Whether the coverage is acceptable for a first build.** Kakamega from August 2026, and three KenyaEMR facilities.

6. **Which missing data to ask DHA for, and who asks.** In order of what it unlocks: the KHIS malaria forms (MOH 705A and B, 706, 710 and inpatient), then county populations, then the list of admitting facilities. LMIS and eCHIS are larger requests.

7. **Indicator 16 (SMC).** It cannot be built, and the guide gives it no definition. The programme would need to define it and name the eCHIS data.

## How this was checked

- Read-only queries on the Trino that holds bronze, on 19 November 2026.
- For each indicator, the tables and fields that would supply its numerator and denominator were looked for, and the records counted.
- Only totals were read. No patient row was viewed or saved, and none is on this page.
- The counts are rounded and are there to show scale. They are not indicator values.
