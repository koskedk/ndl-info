# KEN02 progress updates

Milestone KEN02/FAA64: National data platforms, analytics and decision-use operational.

Updates for the milestone tracker, newest first. Each update has the bullets to paste under Achievements and Progress for each activity.

## 23 November 2026

### KEN02-A02 | Dataset mapping and specifications

**Achievements**

- Access secured to all the data sources: the DHA data lake (KenyaEMR, AMRS and Tiberbu), KHIS aggregate reporting and the KHIS tracker (MPDSR).
- Inventory of the DHA data lake completed: 151 tables, about 1.9 billion rows and 70 GB across the three EMR sources, with row counts, sizes and last load dates.
- RMNCAH-N data map completed: where maternal, newborn, child, family planning and nutrition data sits in each EMR, with a verdict for each of the 20 core indicators.
- Malaria data map completed: codes and test names that identify malaria in each source, volumes by month and county, and an assessment of the 16 priority malaria indicators (8 can be answered now, 7 partly, 1 not yet).
- Staging specifications written for the two sources outside the lake: KHIS monthly aggregates (MOH 711) and MPDSR death notifications and reviews.
- Master Facility List set up for the pilot facilities, linking each source's facility key to its MFL code.
- Data gaps documented and raised as 11 questions for the lake's owners (for example, incomplete KenyaEMR orders and a Tiberbu patient table that is complete only from August 2026).

**Progress**

- Focus has narrowed to two programmes: RMNCAH-N and malaria.
- Malaria mapping is being extended to the sources not yet available: KHIS outpatient, laboratory and immunisation forms, LMIS, eCHIS and population estimates.
- Specifications are being readied for review and approval.

### KEN02-A03 | Dataset integration/staging

**Achievements**

- Five sources staged into the bronze layer for the pilot facilities: Tiberbu, KenyaEMR, AMRS, KHIS aggregates and the KHIS tracker (MPDSR).
- Silver and gold layers built on the staged data, running end to end.
- Seven RMNCAH-N indicators produced by facility, month and source system: ANC clients aged 10 to 19, postnatal care for mother and for newborn within 48 hours, facility maternal, neonatal and perinatal mortality, and maternal death audit.
- Indicator tables loaded into a serving database and connected to a self-service BI tool as a prototype.
- Data-quality checks in place: staged counts reconciled against the source for 1,297 facility-months, with repeated rows removed before counting.
- Access controls applied: personal identifiers are held in a restricted area only, 447 sensitive MPDSR fields are blocked from the analytics layers, and no person-level tables are served to dashboards.

**Progress**

- Building the malaria indicators, starting with the 8 that current data can answer (confirmed cases, test positivity, treatment with ACT, IPTp3 and nets at ANC).
- Tiberbu indicators that need the patient record report from August 2026 onward, pending a full reload of the patient table by DHA.
- Patient matching across systems (Master Patient Index) is planned next.

### To confirm before posting

- **Five datasets:** the five staged sources are counted as the workplan's "five priority datasets". Confirm that matches the approved list.
- **Approval:** no record was found that the specifications are approved, so A02 says "being readied for approval". Change it if sign-off has happened.
- **Scope:** "pilot facilities" is written without a number, because the sample has seven facilities while the Tiberbu bronze on the external Trino covers 196 in Kakamega.
