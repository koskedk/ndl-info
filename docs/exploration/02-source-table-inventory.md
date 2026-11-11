# Source table inventory

Every Iceberg table in the five source folders under `s3://dha-analytics/iceberg/`, as of 11 November 2026.

Figures come from each table's latest Iceberg metadata file (the current snapshot summary), not from counting rows. "Last load" is the date of the most recent snapshot. The same data, plus the column names of every table, is in [table_inventory.csv](table_inventory.csv).

| Folder | Source | Tables | Rows | Size | Last load |
|---|---|---:|---:|---:|---|
| `hmis_kenya_emr_conso` | KenyaEMR, consolidated copy (current) | 53 | 864,257,404 | 23.4 GB | 2026-11-08 |
| `hmis_kenya_emr` | KenyaEMR, per-facility copy (older) | 72 | 1,263,293,871 | 32.9 GB | 2026-10-31 |
| `hmis_ampath_prod` | AMPATH AMRS, production | 41 | 531,516,625 | 13.4 GB | 2026-11-11 |
| `hmis_ampath_uat` | AMPATH AMRS, test copy (stale) | 44 | 642,190,667 | 16.2 GB | 2026-08-27 |
| `hmis_tiberbu_ingestion` | Tiberbu HMIS | 57 | 478,557,669 | 34.2 GB | 2026-11-11 |


## `hmis_kenya_emr_conso`: KenyaEMR, consolidated copy (current)

| Table | Rows | Size (MB) | Data files | Columns | Last load |
|---|---:|---:|---:|---:|---|
| `obs` | 689,590,829 | 17,169.0 | 1,764 | 33 | 2026-11-08 |
| `encounter` | 74,990,769 | 2,423.0 | 652 | 18 | 2026-11-08 |
| `visit_attribute` | 35,196,582 | 1,018.2 | 566 | 14 | 2026-11-08 |
| `visit` | 21,887,033 | 793.7 | 542 | 18 | 2026-11-08 |
| `patient_identifier` | 10,431,742 | 330.4 | 532 | 17 | 2026-11-08 |
| `drug_order` | 8,078,900 | 37.3 | 420 | 19 | 2026-11-08 |
| `location` | 7,401,414 | 205.3 | 542 | 37 | 2026-11-07 |
| `person` | 5,309,913 | 156.5 | 539 | 22 | 2026-11-08 |
| `concept_set` | 2,859,015 | 17.4 | 537 | 8 | 2026-11-07 |
| `medication_dispense` | 1,484,059 | 80.4 | 401 | 35 | 2026-11-08 |
| `encounter_diagnosis` | 1,293,219 | 47.3 | 490 | 20 | 2026-11-08 |
| `stockmgmt_stock_item_transaction` | 1,186,132 | 51.3 | 455 | 18 | 2026-11-08 |
| `iclm_virtual_claim` | 813,273 | 818.4 | 451 | 79 | 2026-11-08 |
| `stockmgmt_stock_item_packaging_uom` | 591,211 | 18.9 | 528 | 14 | 2026-11-08 |
| `encounter_type` | 578,124 | 9.3 | 535 | 15 | 2026-11-08 |
| `iclm_vc_intervention` | 564,724 | 43.4 | 428 | 46 | 2026-11-08 |
| `stockmgmt_stock_item` | 562,286 | 33.5 | 527 | 33 | 2026-11-08 |
| `global_property` | 544,511 | 50.8 | 532 | 14 | 2026-11-08 |
| `concept_name` | 367,842 | 13.4 | 536 | 16 | 2026-11-07 |
| `form` | 106,106 | 9.3 | 534 | 19 | 2026-11-08 |
| `patient_identifier_type` | 86,124 | 5.8 | 535 | 20 | 2026-11-08 |
| `bed_patient_assignment_map` | 59,165 | 4.5 | 179 | 16 | 2026-11-08 |
| `cashier_bill_line_item` | 36,968 | 5.0 | 431 | 21 | 2026-11-08 |
| `orders` | 27,811 | 7.7 | 508 | 34 | 2026-11-08 |
| `location_tag` | 27,308 | 2.8 | 535 | 13 | 2026-11-08 |
| `procedures` | 24,331 | 3.3 | 86 | 46 | 2026-11-08 |
| `visit_attribute_type` | 23,432 | 4.4 | 535 | 19 | 2026-11-08 |
| `bed` | 18,524 | 1.9 | 248 | 14 | 2026-11-08 |
| `location_tag_map` | 18,403 | 0.0 | 4 | 3 | 2026-11-08 |
| `bed_location_map` | 15,702 | 0.3 | 107 | 6 | 2026-11-08 |
| `visit_type` | 12,527 | 3.0 | 535 | 13 | 2026-11-08 |
| `cashier_bill_payment` | 10,623 | 2.9 | 416 | 16 | 2026-11-08 |
| `iclm_vc_bill_line` | 9,803 | 7.7 | 406 | 33 | 2026-11-08 |
| `cashier_bill` | 9,594 | 4.6 | 432 | 26 | 2026-11-08 |
| `concept` | 5,357 | 3.7 | 534 | 18 | 2026-11-07 |
| `relationship_type` | 5,340 | 3.9 | 534 | 16 | 2026-11-08 |
| `stockmgmt_stock_operation` | 4,267 | 7.3 | 466 | 42 | 2026-11-08 |
| `stockmgmt_stock_batch` | 3,956 | 3.5 | 466 | 20 | 2026-11-08 |
| `drug` | 3,204 | 3.9 | 534 | 20 | 2026-11-07 |
| `concept_reference_map` | 2,658 | 2.4 | 532 | 10 | 2026-11-07 |
| `concept_reference_term` | 2,658 | 3.3 | 532 | 16 | 2026-11-07 |
| `stockmgmt_stock_operation_type` | 1,590 | 5.8 | 534 | 29 | 2026-11-08 |
| `bed_type` | 1,547 | 2.9 | 533 | 14 | 2026-11-08 |
| `iclm_claim_intervention` | 1,309 | 0.1 | 20 | 13 | 2026-11-08 |
| `relationship` | 1,154 | 2.3 | 371 | 16 | 2026-11-08 |
| `concept_map_type` | 1,068 | 2.9 | 534 | 14 | 2026-11-08 |
| `order_type` | 1,067 | 3.4 | 534 | 15 | 2026-11-08 |
| `stockmgmt_party` | 978 | 2.6 | 532 | 13 | 2026-11-08 |
| `stockmgmt_stock_source` | 861 | 2.9 | 531 | 14 | 2026-11-08 |
| `iclm_claim` | 677 | 0.5 | 21 | 55 | 2026-11-08 |
| `cashier_payment_mode` | 646 | 2.8 | 523 | 14 | 2026-11-08 |
| `concept_reference_source` | 534 | 3.2 | 534 | 16 | 2026-11-08 |
| `iclm_packages` | 534 | 6.0 | 534 | 31 | 2026-11-08 |

## `hmis_kenya_emr`: KenyaEMR, per-facility copy (older)

| Table | Rows | Size (MB) | Data files | Columns | Last load |
|---|---:|---:|---:|---:|---|
| `obs` | 674,348,728 | 16,484.8 | 2,516 | 33 | 2026-10-15 |
| `concept_reference_map` | 130,942,870 | 1,723.6 | 2,462 | 10 | 2026-10-11 |
| `concept_reference_term` | 110,849,275 | 3,175.5 | 2,462 | 16 | 2026-10-11 |
| `concept_name` | 92,925,705 | 2,449.1 | 2,460 | 16 | 2026-10-11 |
| `encounter` | 73,633,704 | 2,386.6 | 2,350 | 18 | 2026-10-12 |
| `concept` | 48,478,747 | 977.9 | 2,463 | 18 | 2026-10-11 |
| `visit_attribute` | 33,830,604 | 1,180.3 | 2,460 | 14 | 2026-10-11 |
| `visit` | 21,458,446 | 842.4 | 2,364 | 18 | 2026-10-12 |
| `orders` | 17,327,542 | 779.9 | 2,287 | 34 | 2026-10-12 |
| `patient_identifier` | 9,988,323 | 359.1 | 2,390 | 17 | 2026-10-12 |
| `drug` | 9,320,972 | 299.5 | 2,457 | 20 | 2026-10-11 |
| `drug_order` | 8,062,380 | 51.0 | 1,476 | 19 | 2026-10-12 |
| `location` | 7,384,171 | 327.8 | 2,462 | 37 | 2026-10-11 |
| `person` | 5,152,337 | 179.8 | 2,457 | 22 | 2026-10-12 |
| `concept_set` | 2,853,661 | 70.4 | 2,463 | 8 | 2026-10-11 |
| `cashier_bill_line_item` | 2,391,088 | 114.7 | 1,800 | 21 | 2026-10-12 |
| `stockmgmt_stock_item_packaging_uom` | 2,209,613 | 63.9 | 526 | 14 | 2026-10-31 |
| `stockmgmt_stock_item` | 1,592,925 | 80.9 | 525 | 33 | 2026-10-31 |
| `medication_dispense` | 1,248,980 | 90.7 | 1,691 | 35 | 2026-10-12 |
| `cashier_bill_payment` | 1,051,567 | 47.7 | 1,743 | 16 | 2026-10-12 |
| `stockmgmt_stock_item_transaction` | 992,887 | 58.8 | 1,989 | 18 | 2026-10-12 |
| `encounter_diagnosis` | 987,821 | 53.3 | 2,211 | 20 | 2026-10-12 |
| `encounter_provider` | 809,729 | 28.4 | 14 | 14 | 2026-08-23 |
| `cashier_bill` | 807,632 | 58.1 | 1,812 | 26 | 2026-10-12 |
| `iclm_packages` | 575,094 | 36.4 | 534 | 31 | 2026-10-13 |
| `iclm_virtual_claim` | 557,622 | 608.2 | 1,761 | 74 | 2026-10-12 |
| `global_property` | 529,781 | 47.9 | 532 | 14 | 2026-10-11 |
| `encounter_type` | 476,124 | 38.5 | 2,463 | 15 | 2026-10-11 |
| `relationship` | 375,261 | 17.4 | 369 | 16 | 2026-10-29 |
| `iclm_vc_intervention` | 301,680 | 26.7 | 391 | 46 | 2026-10-13 |
| `iclm_vc_bill_line` | 262,551 | 46.1 | 377 | 33 | 2026-10-13 |
| `form` | 177,746 | 13.2 | 548 | 19 | 2026-10-29 |
| `test_order` | 173,367 | 0.5 | 13 | 8 | 2026-08-23 |
| `person_attribute` | 171,596 | 5.9 | 14 | 14 | 2026-08-23 |
| `concept_answer` | 125,825 | 2.5 | 14 | 9 | 2026-08-23 |
| `stockmgmt_stock_operation` | 122,037 | 14.0 | 460 | 42 | 2026-10-31 |
| `person_name` | 102,378 | 4.5 | 14 | 21 | 2026-08-23 |
| `person_address` | 102,236 | 4.4 | 14 | 37 | 2026-08-23 |
| `patient` | 99,639 | 1.2 | 14 | 11 | 2026-08-23 |
| `patient_identifier_type` | 72,232 | 25.4 | 2,462 | 20 | 2026-10-12 |
| `stockmgmt_stock_batch` | 61,210 | 6.0 | 461 | 20 | 2026-10-31 |
| `bed_patient_assignment_map` | 42,486 | 6.8 | 674 | 16 | 2026-10-12 |
| `concept_map_type` | 41,094 | 13.9 | 2,459 | 14 | 2026-10-12 |
| `patient_program` | 37,160 | 1.5 | 13 | 17 | 2026-08-23 |
| `concept_reference_source` | 32,786 | 17.0 | 2,462 | 16 | 2026-10-12 |
| `location_tag` | 26,240 | 14.0 | 2,461 | 13 | 2026-10-12 |
| `concept_numeric` | 23,642 | 0.2 | 14 | 11 | 2026-08-23 |
| `procedures` | 19,906 | 7.1 | 340 | 45 | 2026-10-12 |
| `visit_attribute_type` | 19,693 | 20.2 | 2,460 | 19 | 2026-10-12 |
| `location_tag_map` | 18,381 | 1.0 | 623 | 3 | 2026-10-11 |
| `stockmgmt_party` | 15,267 | 2.9 | 532 | 13 | 2026-10-31 |
| `bed_location_map` | 14,740 | 1.8 | 633 | 6 | 2026-10-12 |
| `bed` | 14,210 | 6.2 | 1,065 | 14 | 2026-10-12 |
| `visit_type` | 10,391 | 13.6 | 2,457 | 13 | 2026-10-12 |
| `relationship_type` | 7,469 | 4.0 | 534 | 16 | 2026-10-29 |
| `stockmgmt_stock_operation_type` | 7,435 | 6.1 | 534 | 29 | 2026-10-31 |
| `bed_type` | 7,369 | 13.2 | 2,461 | 14 | 2026-10-12 |
| `order_type` | 5,988 | 15.6 | 2,459 | 15 | 2026-10-12 |
| `cashier_payment_mode` | 4,763 | 12.8 | 2,373 | 14 | 2026-10-12 |
| `stockmgmt_stock_source` | 2,148 | 3.0 | 530 | 14 | 2026-10-31 |
| `procedure_order` | 1,496 | 0.0 | 3 | 13 | 2026-08-23 |
| `iclm_claim_intervention` | 1,234 | 0.1 | 19 | 13 | 2026-10-13 |
| `provider` | 851 | 0.1 | 14 | 17 | 2026-08-23 |
| `conditions` | 811 | 0.1 | 8 | 23 | 2026-08-23 |
| `person_attribute_type` | 662 | 0.1 | 14 | 18 | 2026-08-23 |
| `iclm_claim` | 633 | 1.8 | 95 | 55 | 2026-10-12 |
| `concept_class` | 476 | 0.1 | 14 | 13 | 2026-08-23 |
| `program` | 286 | 0.1 | 14 | 12 | 2026-08-23 |
| `concept_datatype` | 168 | 0.1 | 14 | 12 | 2026-08-23 |
| `patient_state` | 0 | 0.0 | 0 | 17 | 2026-08-23 |
| `program_workflow` | 0 | 0.0 | 0 | 10 | 2026-08-23 |
| `program_workflow_state` | 0 | 0.0 | 0 | 12 | 2026-08-23 |

## `hmis_ampath_prod`: AMPATH AMRS, production

| Table | Rows | Size (MB) | Data files | Columns | Last load |
|---|---:|---:|---:|---:|---|
| `obs` | 452,340,173 | 11,138.5 | 1,856 | 30 | 2026-11-11 |
| `drug_order` | 21,367,393 | 160.8 | 1,265 | 18 | 2026-11-11 |
| `encounter_provider` | 16,789,200 | 517.6 | 935 | 13 | 2026-11-11 |
| `visit` | 16,473,458 | 618.2 | 1,725 | 16 | 2026-11-11 |
| `encounter` | 16,383,076 | 621.2 | 938 | 16 | 2026-11-11 |
| `patient_identifier` | 2,154,901 | 90.5 | 707 | 16 | 2026-11-11 |
| `encounter__change_date_v2` | 2,036,604 | 99.5 | 1,212 | 17 | 2026-09-29 |
| `person` | 1,322,157 | 52.3 | 657 | 19 | 2026-11-11 |
| `patient` | 1,314,743 | 20.6 | 657 | 10 | 2026-11-11 |
| `orders` | 890,096 | 51.6 | 483 | 32 | 2026-11-11 |
| `concept_name` | 124,041 | 5.6 | 22 | 15 | 2026-11-07 |
| `pharmacy_drug_extra` | 92,080 | 3.8 | 1 | 35 | 2026-11-11 |
| `concept_reference_term` | 56,144 | 2.6 | 1 | 15 | 2026-11-11 |
| `concept` | 51,683 | 1.7 | 31 | 17 | 2026-11-07 |
| `concept_reference_map` | 46,763 | 1.8 | 1 | 9 | 2026-11-11 |
| `concept_set` | 25,904 | 0.8 | 17 | 7 | 2026-11-07 |
| `bill_orders` | 15,819 | 3.5 | 353 | 18 | 2026-11-11 |
| `encounter_diagnosis` | 9,192 | 2.5 | 304 | 19 | 2026-11-11 |
| `claims_queue` | 5,286 | 7.6 | 597 | 16 | 2026-10-14 |
| `claim_line` | 5,093 | 0.4 | 1 | 15 | 2026-11-11 |
| `drug` | 3,308 | 0.2 | 10 | 19 | 2026-09-23 |
| `claim_visit` | 3,297 | 7.3 | 323 | 21 | 2026-11-11 |
| `claim_diagnosis` | 2,963 | 0.2 | 1 | 12 | 2026-11-11 |
| `claim_interventions` | 1,428 | 0.1 | 1 | 13 | 2026-11-11 |
| `location` | 563 | 0.1 | 2 | 36 | 2026-10-08 |
| `encounter_type` | 354 | 0.0 | 2 | 14 | 2026-09-22 |
| `facility_locations` | 202 | 0.0 | 1 | 19 | 2026-11-11 |
| `bed_patient_assignment_map` | 169 | 0.0 | 1 | 15 | 2026-11-11 |
| `visit_type` | 165 | 0.0 | 2 | 12 | 2026-09-22 |
| `facilities` | 93 | 0.0 | 2 | 17 | 2026-10-08 |
| `concept_map_type` | 70 | 0.0 | 1 | 13 | 2026-11-11 |
| `patient_identifier_type` | 62 | 0.0 | 1 | 19 | 2026-09-11 |
| `concept_reference_source` | 41 | 0.0 | 1 | 14 | 2026-11-11 |
| `bed` | 36 | 0.0 | 1 | 13 | 2026-11-11 |
| `bed_location_map` | 32 | 0.0 | 1 | 5 | 2026-11-11 |
| `order_type` | 15 | 0.0 | 2 | 14 | 2026-09-22 |
| `bed_type` | 12 | 0.0 | 1 | 13 | 2026-11-11 |
| `encounter_to_interventions` | 5 | 0.0 | 1 | 2 | 2026-11-11 |
| `fund_types` | 3 | 0.0 | 1 | 5 | 2026-11-11 |
| `insurance_authority` | 1 | 0.0 | 1 | 6 | 2026-11-11 |
| `pre_auth_requests` | 0 | 0.0 | 0 | 25 | - |

## `hmis_ampath_uat`: AMPATH AMRS, test copy (stale)

| Table | Rows | Size (MB) | Data files | Columns | Last load |
|---|---:|---:|---:|---:|---|
| `obs` | 532,733,636 | 12,384.4 | 2,906 | 30 | 2026-08-26 |
| `encounter_provider` | 44,774,973 | 1,413.2 | 1,122 | 13 | 2026-08-26 |
| `encounter` | 39,767,139 | 1,471.8 | 626 | 16 | 2026-08-26 |
| `visit` | 14,857,463 | 551.1 | 743 | 16 | 2026-08-24 |
| `patient_identifier` | 6,164,259 | 247.6 | 309 | 16 | 2026-08-26 |
| `person` | 1,259,503 | 46.1 | 63 | 19 | 2026-08-25 |
| `patient` | 1,252,833 | 17.7 | 63 | 10 | 2026-08-25 |
| `orders` | 778,413 | 40.4 | 26 | 32 | 2026-08-25 |
| `pharmacy_drug_extra` | 276,240 | 11.9 | 15 | 35 | 2026-08-26 |
| `concept_name` | 130,725 | 5.3 | 7 | 15 | 2026-08-25 |
| `concept` | 78,655 | 2.2 | 4 | 17 | 2026-08-25 |
| `concept_reference_map` | 54,215 | 1.6 | 3 | 9 | 2026-08-25 |
| `concept_reference_term` | 52,404 | 2.2 | 3 | 15 | 2026-08-25 |
| `drug_order` | 3,170 | 0.0 | 1 | 18 | 2026-08-25 |
| `concept_set` | 3,017 | 0.1 | 1 | 7 | 2026-08-25 |
| `drug` | 782 | 0.0 | 1 | 19 | 2026-08-25 |
| `facility_locations` | 760 | 0.1 | 4 | 19 | 2026-08-27 |
| `location` | 552 | 0.0 | 1 | 36 | 2026-08-25 |
| `encounter_type` | 353 | 0.0 | 1 | 14 | 2026-08-25 |
| `bill_orders` | 313 | 0.0 | 1 | 18 | 2026-08-27 |
| `encounter_diagnosis` | 215 | 0.0 | 1 | 19 | 2026-08-25 |
| `claim_visit` | 164 | 0.1 | 1 | 21 | 2026-08-27 |
| `visit_type` | 162 | 0.0 | 1 | 12 | 2026-08-25 |
| `bed_patient_assignment_map` | 96 | 0.0 | 1 | 15 | 2026-08-25 |
| `facilities` | 83 | 0.0 | 1 | 17 | 2026-08-27 |
| `claim_line` | 80 | 0.0 | 1 | 15 | 2026-08-27 |
| `claim_interventions` | 71 | 0.0 | 1 | 13 | 2026-08-27 |
| `concept_map_type` | 70 | 0.0 | 1 | 13 | 2026-08-25 |
| `patient_identifier_type` | 61 | 0.0 | 1 | 19 | 2026-08-25 |
| `claim_diagnosis` | 51 | 0.0 | 1 | 12 | 2026-08-27 |
| `claims_queue` | 41 | 0.0 | 1 | 16 | 2026-08-27 |
| `concept_reference_source` | 40 | 0.0 | 1 | 14 | 2026-08-25 |
| `bed` | 38 | 0.0 | 1 | 13 | 2026-08-25 |
| `bed_location_map` | 29 | 0.0 | 1 | 5 | 2026-08-25 |
| `claim_provider_state_trans` | 13 | 0.0 | 1 | 10 | 2026-08-27 |
| `bed_type` | 10 | 0.0 | 1 | 13 | 2026-08-25 |
| `hie_interventions` | 10 | 0.0 | 1 | 28 | 2026-08-27 |
| `pre_auth_requests` | 9 | 0.0 | 1 | 25 | 2026-08-27 |
| `order_type` | 8 | 0.0 | 1 | 14 | 2026-08-25 |
| `claim_payer_state_trans` | 3 | 0.0 | 1 | 11 | 2026-08-27 |
| `fund_types` | 3 | 0.0 | 1 | 5 | 2026-08-27 |
| `encounter_to_interventions` | 2 | 0.0 | 1 | 2 | 2026-08-27 |
| `preauth_provider_state_trans` | 2 | 0.0 | 1 | 11 | 2026-08-27 |
| `insurance_authority` | 1 | 0.0 | 1 | 6 | 2026-08-27 |

## `hmis_tiberbu_ingestion`: Tiberbu HMIS

| Table | Rows | Size (MB) | Data files | Columns | Last load |
|---|---:|---:|---:|---:|---|
| `charge_sheet_item` | 52,122,536 | 2,274.6 | 7,518 | 31 | 2026-11-11 |
| `normal_test_result` | 48,053,458 | 714.0 | 2,283 | 30 | 2026-11-11 |
| `approval_log` | 39,956,567 | 1,040.7 | 6,394 | 17 | 2026-11-11 |
| `queue_state_movements` | 27,557,523 | 2,749.1 | 7,335 | 26 | 2026-11-11 |
| `doctors_notes` | 27,174,062 | 1,653.1 | 6,950 | 25 | 2026-11-11 |
| `patient_encounter` | 25,288,421 | 1,649.8 | 7,425 | 40 | 2026-11-11 |
| `charge_sheet` | 24,565,770 | 1,680.0 | 7,422 | 55 | 2026-11-11 |
| `scheme_claim` | 24,204,138 | 3,801.0 | 6,748 | 46 | 2026-11-11 |
| `queue_state` | 20,710,846 | 2,232.1 | 7,353 | 39 | 2026-11-11 |
| `diagnosis_entry` | 19,052,080 | 662.3 | 7,272 | 23 | 2026-11-11 |
| `item` | 17,697,125 | 1,010.3 | 4,661 | 98 | 2026-11-11 |
| `patient_bill` | 16,370,822 | 826.1 | 7,297 | 41 | 2026-11-11 |
| `doctor_drug_prescription` | 15,173,840 | 1,045.6 | 7,163 | 57 | 2026-11-11 |
| `customer_insurance_schemes` | 13,367,146 | 686.7 | 6,888 | 37 | 2026-11-11 |
| `patient_appointment` | 13,260,171 | 1,224.0 | 7,362 | 78 | 2026-11-11 |
| `drug_prescription` | 13,165,448 | 800.4 | 7,012 | 41 | 2026-11-11 |
| `stock_ledger_entry` | 9,834,927 | 682.1 | 7,166 | 43 | 2026-11-11 |
| `patient` | 8,707,251 | 1,191.5 | 7,430 | 94 | 2026-11-11 |
| `vital_signs` | 8,049,816 | 851.5 | 7,037 | 63 | 2026-11-11 |
| `form_data_repository` | 7,931,765 | 776.4 | 6,831 | 24 | 2026-11-11 |
| `stock_entry` | 7,574,402 | 415.9 | 2,097 | 72 | 2026-11-11 |
| `prescription_mart_insert_table` | 7,272,291 | 418.0 | 8 | 26 | 2026-07-09 |
| `biometric_transaction` | 6,063,450 | 1,527.0 | 6,678 | 38 | 2026-11-11 |
| `lab_test` | 3,768,904 | 485.6 | 6,740 | 76 | 2026-11-11 |
| `lab_prescription` | 3,734,322 | 254.0 | 6,799 | 32 | 2026-11-11 |
| `bin` | 2,862,793 | 208.5 | 7,146 | 27 | 2026-11-11 |
| `health_program_enrollment` | 2,715,684 | 119.8 | 2,230 | 25 | 2026-11-11 |
| `custom_lab_results` | 2,290,030 | 95.4 | 2,193 | 17 | 2026-11-11 |
| `clinical_procedure` | 2,115,359 | 443.8 | 6,043 | 54 | 2026-11-11 |
| `procedure_prescription` | 1,320,355 | 194.7 | 6,803 | 38 | 2026-11-11 |
| `inpatient_occupancy` | 1,268,842 | 133.1 | 7,410 | 18 | 2026-11-11 |
| `payment_entry` | 1,166,875 | 348.4 | 5,985 | 90 | 2026-11-11 |
| `stock_reconciliation` | 1,058,202 | 46.0 | 1,685 | 26 | 2026-11-11 |
| `company_settings` | 778,775 | 753.3 | 6,554 | 133 | 2026-11-11 |
| `inpatient_medication_order` | 564,880 | 110.3 | 5,589 | 31 | 2026-11-11 |
| `inpatient_record` | 369,311 | 428.9 | 6,839 | 124 | 2026-11-11 |
| `healthcare_practitioner` | 368,808 | 161.9 | 6,489 | 51 | 2026-11-11 |
| `healthcare_service_unit` | 315,333 | 206.7 | 6,671 | 69 | 2026-11-11 |
| `codification_table` | 271,265 | 12.7 | 422 | 19 | 2026-11-11 |
| `inpatient_medication_entry` | 156,046 | 31.8 | 2,835 | 28 | 2026-11-11 |
| `clinical_procedure_template` | 125,995 | 11.8 | 105 | 46 | 2026-11-11 |
| `inpatient_transfer` | 58,786 | 56.9 | 4,449 | 28 | 2026-11-11 |
| `item_group` | 18,680 | 1.3 | 56 | 23 | 2026-11-10 |
| `patient_referral` | 18,079 | 81.5 | 2,663 | 42 | 2026-11-11 |
| `county_administrative_unit` | 12,571 | 0.6 | 9 | 22 | 2026-10-06 |
| `warehouse` | 9,042 | 7.2 | 565 | 34 | 2026-11-11 |
| `description_reports_mapping_procedures` | 8,450 | 0.5 | 44 | 12 | 2026-11-04 |
| `sha_intervention` | 7,435 | 1.7 | 91 | 38 | 2026-08-19 |
| `description_reports_mapping` | 6,809 | 0.9 | 48 | 29 | 2026-11-10 |
| `death_notification` | 4,335 | 96.1 | 1,673 | 148 | 2026-11-11 |
| `medical_department` | 3,487 | 0.5 | 48 | 20 | 2026-11-10 |
| `description_reports_mapping_special_clinics` | 2,964 | 0.7 | 109 | 13 | 2026-11-11 |
| `diagnosis` | 1,105 | 0.1 | 4 | 14 | 2026-08-04 |
| `description_reports_mapping_forms` | 128 | 0.2 | 41 | 12 | 2026-11-05 |
| `healthcare_service_unit_type` | 95 | 0.3 | 22 | 33 | 2026-11-10 |
| `ward_well_persons` | 68 | 0.1 | 12 | 17 | 2026-11-05 |
| `description_reports_mapping_labs` | 1 | 0.0 | 1 | 12 | 2026-11-05 |
