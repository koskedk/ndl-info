# Malaria diagnoses and tests in the lake, by month and county

This page counts what malaria data the three EMR sources in the lake actually hold: how many malaria diagnoses and malaria tests there are, and what share they are of all diagnoses and all tests, for each month and county. It covers the twelve complete months from November 2025 to October 2026.

It follows [03-malaria-data-map.md](03-malaria-data-map.md), which said where the data sits. This page says how much is there and which values mean malaria.

**What has been checked.** Every figure was counted from the lake on 16 and 17 November 2026. Only totals were produced: no individual record was viewed or saved. Diagnosis and test names were read as lists of distinct values with their counts.

All counts for every county and month are in two spreadsheets beside this page:

- [malaria_diagnoses_by_month_county.csv](malaria_diagnoses_by_month_county.csv)
- [malaria_tests_by_month_county.csv](malaria_tests_by_month_county.csv)

Each row is one source, month and county, with the total, the malaria count and the malaria share. The diagnoses file says how the diagnosis was recorded (`recorded_as`). The tests file says which stage the row counts (`stage`: ordered, done, or results recorded) and splits malaria tests into rapid test and microscopy. KenyaEMR's "malaria test results recorded" rows have no total, for the reason given in the KenyaEMR section.

## Summary

| Source | Counties covered | All diagnoses | Malaria diagnoses | Rate | All tests ordered | Malaria tests ordered | Rate |
|---|---|---:|---:|---:|---:|---:|---:|
| Tiberbu | 42 | 16,522,132 | 544,734 | 3.3% | 2,968,622 | 472,207 | 15.9% |
| KenyaEMR | Kisumu, Siaya, Kilifi | 1,046,327 | 96,702 | 9.2% | 790,083 | 177,680 | 22.5% |
| AMRS | Uasin Gishu for malaria | 8,577 | 92 | 1.1% | 81,512 | 728 | 0.9% |

Malaria tests by method:

| Source | Stage | Microscopy | Rapid diagnostic test | Other |
|---|---|---:|---:|---:|
| Tiberbu | Tests ordered | 290,859 | 177,251 | 4,097 |
| Tiberbu | Tests done | 293,291 | 173,340 | 4,051 |
| KenyaEMR | Tests ordered | 138,517 | 39,071 | 92 |
| KenyaEMR | Results recorded | 131,088 | 34,108 | 40 |
| AMRS | Tests ordered | 536 | 192 | 0 |

"Other" is tests named "Malaria test (MPS/mRDT)" with no method stated in Tiberbu, and malaria PCR in KenyaEMR.

Main findings:

1. **The lake holds about 640,000 malaria diagnoses and 650,000 malaria tests for the year**, almost all from Tiberbu and KenyaEMR. AMRS holds almost none.
2. **The two large sources cover different counties.** Tiberbu covers 42 counties but not Kisumu, Siaya, Homa Bay, Kilifi or Murang'a. KenyaEMR supplies Kisumu, Siaya and Kilifi. Nothing in the lake covers Homa Bay or Murang'a.
3. **The rate per county is steady; the counts are not.** Monthly counts rise steeply through the year because facilities came onto the systems and because of how the lake was loaded, not because of disease. Within a county the malaria share of diagnoses barely moves: Vihiga stays between 13% and 19%, Mombasa at about 1%. Compare rates, not counts.
4. **The counties rank as expected.** The malaria share of diagnoses is highest in Migori (26.9%), Turkana (26.8%), Bungoma (20.9%), Busia (20.1%), Kisumu (16.1%), Vihiga (15.3%), Kakamega (14.3%) and Siaya (14.1%), and under 1% across the central highlands.
5. **ICD-10 codes cannot be used.** Tiberbu codes diagnoses in ICD-11. KenyaEMR and AMRS store a concept, and the link from concept to ICD code is not in the lake. Malaria was therefore matched on ICD-11 codes in Tiberbu and on the diagnosis name in the other two.
6. **The keywords need care.** "Malaria" also matches HIV diagnoses named "without mention of tuberculosis or malaria", and "microscopy" also matches urine, sputum and stool tests. Both were excluded, as set out below.
7. **Malaria species cannot be read from the codes.** The most-used Tiberbu code is "Plasmodium malariae malaria without complication", with 43% of malaria entries, where falciparum would be expected.

## How malaria was identified

### Diagnoses

| Source | Table | A diagnosis counts as malaria when | Dated by |
|---|---|---|---|
| Tiberbu | `diagnosis_entry` | its code is ICD-11 1F40 to 1F45 or 1F4Z, or its code title or reporting group mentions malaria | date the entry was created |
| KenyaEMR | `encounter_diagnosis` | the coded diagnosis has a name mentioning malaria or plasmodium, or the free-text diagnosis mentions them | encounter date |
| AMRS | `encounter_diagnosis`, and coded answers in `obs` | as KenyaEMR | encounter or observation date |

Three groups of matches were left out because they are not a diagnosis of malaria:

- **HIV diagnoses that only mention malaria in the name**, such as "HIV disease clinical stage 1 without mention of tuberculosis or malaria": 16,311 entries in KenyaEMR.
- **"HIV disease associated with malaria"**: 1,782 entries in KenyaEMR. These are kept apart and can be added back if wanted.
- **"Tested for Malaria"** in Tiberbu, which sits on a laboratory-examination code (QA00.C): 755 entries.

The ICD-10 malaria codes (B50 to B54, P37.3 and P37.4) were searched for and none was found in any source.

### Tests

| Source | Tests ordered | Tests done or results | Dated by |
|---|---|---|---|
| Tiberbu | `lab_prescription` | `lab_test` | date created; test date |
| KenyaEMR | `orders` in the older copy (`hmis_kenya_emr`), test orders only | results in `obs` | date ordered; observation date |
| AMRS | `orders`, test orders only | test results in `obs` | date ordered; observation date |

A test counts as a malaria test when its name is one of:

- **Rapid diagnostic test:** Malaria Rapid Diagnostic Test, Malaria RDT, mRDT, mRDT for malaria, Malaria Rapid Test, Rapid malaria test.
- **Microscopy:** Malaria BS, Blood slide for Malaria, Malaria Blood Smear, Malaria Microscopy, Blood Smear for Malaria Parasites, BS for MPS, Malarial Smear, and "Blood smear for parasites".
- **Method not stated:** Malaria test (MPS/mRDT).

"Blood smear for parasites" does not name malaria. It is counted as malaria microscopy (39,719 tests done in Tiberbu) because that is its ordinary use; take it out if a strict reading is wanted.

## Tiberbu

### By month

| Month | Counties | All diagnoses | Malaria | Rate | Tests ordered | Malaria | Rate | Tests done | Malaria | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nov 2025 | 18 | 133,148 | 466 | 0.3% | 55,691 | 5,324 | 9.6% | 55,204 | 5,259 | 9.5% |
| Dec 2025 | 23 | 130,459 | 477 | 0.4% | 46,149 | 3,868 | 8.4% | 45,419 | 3,733 | 8.2% |
| Jan 2026 | 26 | 186,826 | 3,510 | 1.9% | 61,331 | 8,142 | 13.3% | 61,145 | 7,838 | 12.8% |
| Feb 2026 | 28 | 268,002 | 7,950 | 3.0% | 83,376 | 15,861 | 19.0% | 81,788 | 15,423 | 18.9% |
| Mar 2026 | 29 | 270,675 | 9,559 | 3.5% | 70,496 | 16,999 | 24.1% | 69,107 | 16,540 | 23.9% |
| Apr 2026 | 32 | 422,198 | 13,702 | 3.2% | 72,380 | 17,595 | 24.3% | 68,072 | 16,652 | 24.5% |
| May 2026 | 35 | 566,150 | 20,336 | 3.6% | 81,299 | 21,837 | 26.9% | 76,493 | 20,797 | 27.2% |
| Jun 2026 | 39 | 520,606 | 19,674 | 3.8% | 68,127 | 18,639 | 27.4% | 56,560 | 15,157 | 26.8% |
| Jul 2026 | 42 | 1,069,003 | 26,942 | 2.5% | 119,827 | 19,949 | 16.6% | 114,611 | 18,745 | 16.4% |
| Aug 2026 | 42 | 2,339,215 | 57,733 | 2.5% | 398,335 | 45,295 | 11.4% | 419,201 | 46,855 | 11.2% |
| Sep 2026 | 42 | 4,534,685 | 152,859 | 3.4% | 783,719 | 116,082 | 14.8% | 805,782 | 118,592 | 14.7% |
| Oct 2026 | 42 | 6,081,165 | 231,526 | 3.8% | 1,127,892 | 182,616 | 16.2% | 1,145,096 | 185,091 | 16.2% |

### By county, twelve months

| County | All diagnoses | Malaria | Rate | All tests done | Malaria tests | Rate | Rapid test | Microscopy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Vihiga | 807,777 | 123,425 | 15.3% | 164,369 | 88,904 | 54.1% | 57,994 | 30,910 |
| Kakamega | 658,455 | 94,367 | 14.3% | 131,211 | 56,205 | 42.8% | 27,560 | 28,645 |
| Bungoma | 382,970 | 80,056 | 20.9% | 116,501 | 47,473 | 40.7% | 10,477 | 36,996 |
| Migori | 253,755 | 68,180 | 26.9% | 79,244 | 31,429 | 39.7% | 17,865 | 13,564 |
| Turkana | 135,585 | 36,329 | 26.8% | 39,584 | 17,641 | 44.6% | 5,767 | 11,874 |
| Busia | 114,482 | 22,995 | 20.1% | 35,889 | 16,135 | 45.0% | 7,098 | 9,037 |
| Nandi | 653,594 | 16,135 | 2.5% | 105,301 | 18,420 | 17.5% | 3,817 | 14,603 |
| Kisii | 203,081 | 15,201 | 7.5% | 61,611 | 15,876 | 25.8% | 3,687 | 12,189 |
| Mombasa | 1,071,244 | 10,034 | 0.9% | 234,504 | 45,171 | 19.3% | 6,891 | 34,229 |
| Kericho | 349,832 | 9,901 | 2.8% | 80,221 | 11,285 | 14.1% | 2,123 | 9,162 |
| Kwale | 164,103 | 8,951 | 5.5% | 55,806 | 11,891 | 21.3% | 3,296 | 8,595 |
| Baringo | 231,244 | 6,864 | 3.0% | 41,820 | 6,277 | 15.0% | 1,271 | 5,006 |
| Nairobi | 1,352,676 | 6,786 | 0.5% | 181,191 | 6,923 | 3.8% | 2,033 | 4,890 |
| West Pokot | 101,136 | 5,967 | 5.9% | 29,052 | 5,636 | 19.4% | 249 | 5,387 |
| Elgeyo Marakwet | 249,547 | 4,752 | 1.9% | 24,680 | 3,270 | 13.2% | 399 | 2,871 |
| Nyamira | 139,452 | 4,388 | 3.1% | 27,999 | 6,733 | 24.0% | 2,634 | 4,099 |
| Uasin Gishu | 349,705 | 4,233 | 1.2% | 63,744 | 7,915 | 12.4% | 1,581 | 6,334 |
| Bomet | 662,781 | 3,362 | 0.5% | 86,459 | 7,029 | 8.1% | 1,337 | 5,692 |
| Samburu | 127,168 | 2,832 | 2.2% | 15,826 | 2,171 | 13.7% | 157 | 2,014 |
| Trans Nzoia | 47,050 | 2,437 | 5.2% | 17,238 | 3,096 | 18.0% | 694 | 2,402 |
| Nakuru | 956,668 | 2,421 | 0.3% | 106,809 | 4,827 | 4.5% | 1,475 | 3,352 |
| Narok | 80,414 | 2,314 | 2.9% | 19,059 | 3,341 | 17.5% | 497 | 2,844 |
| Tana River | 74,274 | 2,084 | 2.8% | 19,947 | 3,584 | 18.0% | 462 | 3,122 |
| Meru | 280,110 | 1,635 | 0.6% | 96,066 | 6,778 | 7.1% | 4,329 | 2,449 |
| Garissa | 232,286 | 1,459 | 0.6% | 49,458 | 3,821 | 7.7% | 929 | 2,892 |
| Mandera | 64,834 | 1,234 | 1.9% | 23,171 | 2,591 | 11.2% | 379 | 2,212 |
| Taita Taveta | 565,691 | 1,046 | 0.2% | 88,120 | 11,938 | 13.5% | 2,651 | 9,287 |
| Makueni | 1,597,753 | 859 | 0.1% | 339,841 | 7,542 | 2.2% | 1,890 | 5,652 |
| Kiambu | 585,118 | 628 | 0.1% | 142,452 | 2,064 | 1.4% | 446 | 1,618 |
| Tharaka Nithi | 334,875 | 556 | 0.2% | 38,426 | 2,913 | 7.6% | 257 | 2,656 |
| Kirinyaga | 661,793 | 513 | 0.1% | 57,835 | 2,687 | 4.6% | 187 | 2,500 |
| Wajir | 103,752 | 493 | 0.5% | 11,325 | 1,013 | 8.9% | 358 | 655 |
| Embu | 543,127 | 467 | 0.1% | 38,026 | 1,447 | 3.8% | 129 | 1,318 |
| Marsabit | 51,809 | 461 | 0.9% | 17,447 | 1,279 | 7.3% | 168 | 1,111 |
| Nyeri | 1,253,995 | 344 | 0.0% | 134,723 | 794 | 0.6% | 169 | 625 |
| Kajiado | 318,884 | 318 | 0.1% | 68,673 | 1,375 | 2.0% | 675 | 700 |
| Machakos | 252,368 | 235 | 0.1% | 43,655 | 721 | 1.7% | 205 | 516 |
| Kitui | 208,989 | 200 | 0.1% | 62,553 | 1,251 | 2.0% | 609 | 642 |
| Laikipia | 70,384 | 100 | 0.1% | 10,819 | 372 | 3.4% | 131 | 241 |
| Lamu | 45,743 | 73 | 0.2% | 6,459 | 436 | 6.8% | 338 | 98 |
| Isiolo | 4,619 | 50 | 1.1% | 2,418 | 186 | 7.7% | 87 | 99 |
| Nyandarua | 179,009 | 49 | 0.0% | 28,946 | 242 | 0.8% | 39 | 203 |

### Which codes were matched

| Code | Title | Entries |
|---|---|---:|
| 1F42.Z | Plasmodium malariae malaria without complication | 234,724 |
| 1F4Z | Malaria, unspecified | 148,901 |
| 1F45 | Malaria without parasitological confirmation | 108,684 |
| 1F40.Z | Malaria due to Plasmodium falciparum, unspecified | 38,366 |
| 1F44 | Other parasitologically confirmed malaria | 7,512 |
| 1F42.Y | Malaria due to Plasmodium malariae with other complications | 1,974 |
| 1F40.Y | Other severe and complicated Plasmodium falciparum malaria | 1,874 |
| JB63.60 | Malaria complicating pregnancy, childbirth, or the puerperium | 1,033 |
| 1F43 | Malaria due to Plasmodium ovale | 739 |
| 1F40.0 | Plasmodium falciparum malaria with cerebral complications | 505 |
| 1F41.Z | Plasmodium vivax malaria without complication | 264 |
| 1F41.Y | Malaria due to Plasmodium vivax with other complications | 79 |
| 1F42.0 | Plasmodium malariae malaria with nephropathy | 63 |
| 1F41.0 | Plasmodium vivax malaria with rupture of spleen | 11 |
| 1F41 | Malaria due to Plasmodium vivax | 4 |
| 1F42 | Malaria due to Plasmodium malariae | 1 |

Each entry also carries a reporting group. Of the 544,734 malaria entries, 234,342 are grouped as "Suspected Malaria", 111,967 as "Confirmed malaria", 1,026 as "Malaria in Pregnancy" and 197,397 have no group.

### Which test names were matched

Names are shown as stored, in lower case, for tests done. Names with fewer than 1,000 tests that are not malaria tests are left out.

| Test name as stored | Counted as | Tests done |
|---|---|---:|
| malaria bs | microscopy | 210,132 |
| malaria rapid diagnostic test | rapid diagnostic test | 162,623 |
| blood smear for parasites | microscopy | 39,719 |
| blood slide for malaria | microscopy | 25,161 |
| malaria blood smear | microscopy | 9,211 |
| malaria microscopy | microscopy | 9,066 |
| malaria test (mps/mrdt) | malaria test, method not stated | 4,051 |
| malaria rdt | rapid diagnostic test | 3,826 |
| mrdt | rapid diagnostic test | 2,729 |
| mrdt for malaria | rapid diagnostic test | 2,380 |
| malaria rapid test | rapid diagnostic test | 1,551 |
| rapid diagnostic test (rdt)- malaria | rapid diagnostic test | 169 |
| rapid malaria test | rapid diagnostic test | 62 |
| b/s | microscopy | 2 |
| urinalysis and microscopy | not a malaria test | 76,205 |
| urine microscopic examination | not a malaria test | 31,578 |
| hvs microscopy | not a malaria test | 7,287 |
| sputum fm microscopy | not a malaria test | 5,039 |
| urine microscopy | not a malaria test | 3,671 |
| stool microscopy | not a malaria test | 2,432 |
| urine microscopic/macroscopic examination | not a malaria test | 1,712 |
| sputum microscopy | not a malaria test | 1,035 |

### Warnings

- **Early months are thin.** Until June 2026 most counties show almost no malaria diagnoses, then counts jump: Kakamega has 86 in June, 2,536 in July and 43,325 in October. This fits the earlier finding that the lake's Tiberbu tables mostly hold rows created or changed since loading began in late July 2026, together with facilities joining Tiberbu during the year. Only Vihiga and Mombasa have steady figures from early 2026. For comparing counties, use August to October 2026.
- **The falciparum question.** Code 1F42.Z, "Plasmodium malariae malaria without complication", has 234,724 entries against 38,366 for the falciparum code 1F40.Z. This looks like a habit of picking the first "malaria without complication" entry in the list. Do not report species from these codes.
- **Most malaria diagnoses are marked suspected.** 447,082 of the 544,734 entries (82%) have the suspected flag set.
- **There are more malaria diagnoses than malaria tests.** October 2026 has 231,526 diagnoses and 185,091 tests done. Either many cases are diagnosed without a test, or tests are done outside the lab module.
- **"Tests done" includes drafts.** Of 2,998,478 lab test records, 942,228 (31%) are still in Draft status. For malaria tests it is 92,641 of 470,682 (20%).
- **Repeated rows are few.** 16,594,800 loaded rows hold 16,522,132 distinct diagnosis entries (0.4% extra copies). All counts here are of distinct entries.

## KenyaEMR

The KenyaEMR copy in the lake is three counties. Of the facilities that recorded a diagnosis in the year, 169 are in Siaya, 159 in Kisumu and 151 in Kilifi, with one each in Kajiado and Migori.

### By month

| Month | Facilities | All diagnoses | Malaria | Rate | Tests ordered | Malaria | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nov 2025 | 115 | 17,526 | 3,824 | 21.8% | 56,732 | 8,971 | 15.8% |
| Dec 2025 | 104 | 17,615 | 3,686 | 20.9% | 48,257 | 9,623 | 19.9% |
| Jan 2026 | 115 | 15,254 | 3,511 | 23.0% | 56,992 | 10,313 | 18.1% |
| Feb 2026 | 142 | 22,711 | 4,502 | 19.8% | 59,420 | 11,928 | 20.1% |
| Mar 2026 | 170 | 43,730 | 7,872 | 18.0% | 65,161 | 14,580 | 22.4% |
| Apr 2026 | 165 | 38,640 | 5,127 | 13.3% | 64,747 | 11,189 | 17.3% |
| May 2026 | 279 | 59,356 | 10,638 | 17.9% | 73,804 | 17,734 | 24.0% |
| Jun 2026 | 330 | 107,627 | 12,601 | 11.7% | 88,514 | 22,843 | 25.8% |
| Jul 2026 | 400 | 102,337 | 9,414 | 9.2% | 76,528 | 19,243 | 25.1% |
| Aug 2026 | 362 | 123,119 | 5,634 | 4.6% | 56,653 | 12,408 | 21.9% |
| Sep 2026 | 380 | 204,257 | 11,454 | 5.6% | 97,802 | 25,331 | 25.9% |
| Oct 2026 | 412 | 294,155 | 18,439 | 6.3% | 45,473 | 13,517 | 29.7% |

Test orders stop on 12 October 2026, so October is a part month.

### By county, twelve months

| County | All diagnoses | Malaria | Rate | Tests ordered | Malaria | Rate | Rapid test | Microscopy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Kilifi | 486,279 | 9,625 | 2.0% | 175,078 | 28,944 | 16.5% | 8,070 | 20,852 |
| Kisumu | 403,908 | 65,057 | 16.1% | 424,395 | 113,440 | 26.7% | 20,384 | 93,009 |
| Siaya | 155,671 | 21,959 | 14.1% | 189,913 | 35,236 | 18.6% | 10,558 | 24,655 |

### Malaria test results

A blood smear result is the "Malaria Parasites" line of the smear (answers: No Malaria Parasites, MPS Seen, Positive). A rapid test result is the "Malaria Rapid Test" line (Negative, Positive, Invalid).

| County | Smear results | Positive | Rate | Rapid test results | Positive | Rate |
|---|---:|---:|---:|---:|---:|---:|
| Kilifi | 21,856 | 6,383 | 29.2% | 6,716 | 623 | 9.3% |
| Kisumu | 80,076 | 16,516 | 20.6% | 18,390 | 4,337 | 23.6% |
| Siaya | 29,155 | 3,515 | 12.1% | 8,954 | 2,989 | 33.4% |

| Month | Smear results | Positive | Rapid test results | Positive |
|---|---:|---:|---:|---:|
| Nov 2025 | 6,764 | 1,053 | 1,517 | 514 |
| Dec 2025 | 6,818 | 1,240 | 1,739 | 535 |
| Jan 2026 | 7,538 | 1,267 | 1,905 | 527 |
| Feb 2026 | 8,127 | 1,328 | 1,785 | 478 |
| Mar 2026 | 8,356 | 1,320 | 2,132 | 538 |
| Apr 2026 | 6,387 | 987 | 1,754 | 320 |
| May 2026 | 10,301 | 2,132 | 3,726 | 1,139 |
| Jun 2026 | 12,072 | 2,181 | 6,474 | 1,796 |
| Jul 2026 | 10,338 | 1,694 | 2,929 | 638 |
| Aug 2026 | 6,810 | 907 | 1,764 | 225 |
| Sep 2026 | 19,639 | 6,844 | 3,309 | 440 |
| Oct 2026 | 27,938 | 5,461 | 5,074 | 819 |

Over the year 26,414 of 131,088 smear results (20.1%) and 7,969 of 34,108 rapid test results (23.4%) were positive.

### Which diagnosis names were matched

The fourteen most frequent names that mention malaria, and how each was counted. In all, 45 names were counted as malaria.

| Diagnosis name | Counted as | Entries |
|---|---|---:|
| Malaria, unspecified | malaria | 75,235 |
| HIV disease clinical stage 1 without mention of tuberculosis or malaria | not malaria (name only mentions it) | 12,514 |
| Malaria due to Plasmodium falciparum | malaria | 4,781 |
| Malaria without parasitological confirmation | malaria | 4,656 |
| Other parasitologically confirmed malaria | malaria | 3,150 |
| Human immunodeficiency virus disease without mention of tuberculosis or malaria | not malaria (name only mentions it) | 2,644 |
| Malaria due to Plasmodium falciparum, unspecified | malaria | 1,870 |
| Plasmodium malariae malaria without complication | malaria | 1,481 |
| HIV disease clinical stage 1 associated with malaria | HIV disease associated with malaria | 1,082 |
| Malaria due to Plasmodium malariae | malaria | 953 |
| Other severe and complicated Plasmodium falciparum malaria | malaria | 798 |
| HIV disease clinical stage 2 without mention of tuberculosis or malaria | not malaria (name only mentions it) | 657 |
| Uncomplicated malaria | malaria | 574 |
| Plasmodium Falciparum Malaria with Cerebral Complications | malaria | 498 |

### Warnings

- **The falling overall rate is a change of mix.** Until April nearly all diagnoses came from Kisumu. From June, Kilifi facilities came on in volume at about 2% malaria and pulled the overall rate down from about 20% to about 6%. Read the rate per county.
- **Diagnosis recording grew through the year**, from 115 facilities in November 2025 to 412 in October 2026.
- **Test orders come from the older copy.** The current copy's `orders` table holds only loads since 7 November 2026. The older copy (`hmis_kenya_emr`) stops on 12 October 2026, so there are no orders after that date.
- **There is no "all tests" total from results.** Observations tied to an order rise from about 180,000 a month to 1.9 million in October 2026 while test orders do not, so they cannot serve as a count of all test results. The KenyaEMR test rate is therefore given from orders only.
- **Malaria diagnoses sit in `encounter_diagnosis` only.** The coded questions in `obs` that look like diagnoses (problem list, newly diagnosed disease: about 1.4 million answers in the year) contain no malaria. Malaria does appear about 600 times as a coded chief complaint, which is not counted here.
- **Repeated rows are material.** 1,092,474 loaded diagnosis rows hold 1,046,327 distinct diagnoses (4% extra copies), and September 2026 alone has 16% extra. Malaria test result rows have about 10% extra copies in September. All malaria counts here are of distinct rows.
- **County comes from each facility's own default location.** KenyaEMR tables carry no county column. This is a stand-in until the Master Facility List places each facility database.

## AMRS

AMRS holds almost no malaria data, and what it holds is in Uasin Gishu.

| | All | Malaria |
|---|---:|---:|
| Diagnosis entries (`encounter_diagnosis`, from January 2026) | 8,577 | 92 |
| Diagnoses recorded as coded answers | 5,326 | 6 |
| Tests ordered | 81,512 | 728 (536 smear, 192 rapid test) |
| Test results recorded | 188,734 | 454 (356 smear, 98 rapid test) |

- All 92 malaria diagnosis entries, all 728 malaria test orders and all 454 malaria test results are in Uasin Gishu. Busia, Bungoma, Trans Nzoia, Nandi, West Pokot and Elgeyo Marakwet have test orders but no malaria tests.
- Malaria is recorded as a cause of death in about 90 observations. These are not counted as diagnoses.
- The insurance claim table holds 6 claims with a malaria code out of about 3,200.

## Month by county

The fifteen county and source pairs with the most malaria diagnoses. Empty cells mean nothing was recorded. Tests are tests done for Tiberbu and tests ordered for KenyaEMR. All other counties are in the two spreadsheets.

### Malaria diagnoses

| County | Source | Nov 25 | Dec 25 | Jan 26 | Feb 26 | Mar 26 | Apr 26 | May 26 | Jun 26 | Jul 26 | Aug 26 | Sep 26 | Oct 26 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vihiga | Tiberbu |  | 100 | 2,904 | 6,929 | 8,765 | 12,235 | 18,244 | 17,599 | 16,700 | 6,529 | 14,910 | 18,510 |
| Kakamega | Tiberbu | 1 | 2 | 37 | 29 | 13 | 33 | 54 | 86 | 2,536 | 14,781 | 33,470 | 43,325 |
| Bungoma | Tiberbu |  | 8 | 12 | 25 | 34 | 50 | 77 | 168 | 912 | 3,468 | 29,578 | 45,724 |
| Migori | Tiberbu | 7 | 8 | 17 | 20 | 43 | 55 | 97 | 165 | 1,565 | 9,564 | 19,883 | 36,756 |
| Kisumu | KenyaEMR | 3,808 | 3,603 | 3,369 | 4,327 | 7,297 | 4,440 | 6,713 | 6,374 | 4,872 | 2,128 | 6,852 | 11,274 |
| Turkana | Tiberbu |  | 0 | 4 | 2 | 19 | 18 | 22 | 46 | 894 | 7,248 | 11,534 | 16,542 |
| Busia | Tiberbu |  |  |  | 4 | 4 | 12 | 7 | 43 | 210 | 396 | 5,660 | 16,659 |
| Siaya | KenyaEMR | 16 | 73 | 109 | 173 | 542 | 583 | 3,673 | 5,312 | 3,072 | 1,569 | 2,367 | 4,470 |
| Nandi | Tiberbu | 1 | 2 | 12 | 1 | 2 | 6 | 11 | 55 | 119 | 2,092 | 6,391 | 7,443 |
| Kisii | Tiberbu |  |  |  |  |  | 6 | 5 | 12 | 243 | 2,883 | 5,443 | 6,609 |
| Mombasa | Tiberbu | 383 | 261 | 205 | 536 | 406 | 872 | 1,356 | 1,118 | 824 | 528 | 1,281 | 2,264 |
| Kericho | Tiberbu | 0 | 0 | 1 | 2 | 4 | 14 | 12 | 21 | 90 | 440 | 3,986 | 5,331 |
| Kilifi | KenyaEMR | 0 | 10 | 33 | 2 | 33 | 104 | 204 | 908 | 1,466 | 1,937 | 2,235 | 2,693 |
| Kwale | Tiberbu |  |  |  |  |  |  |  | 8 | 38 | 14 | 2,522 | 6,369 |
| Baringo | Tiberbu |  | 0 | 1 | 0 | 2 | 4 | 3 | 3 | 191 | 1,210 | 2,069 | 3,381 |

### Malaria diagnoses as a share of all diagnoses

| County | Source | Nov 25 | Dec 25 | Jan 26 | Feb 26 | Mar 26 | Apr 26 | May 26 | Jun 26 | Jul 26 | Aug 26 | Sep 26 | Oct 26 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vihiga | Tiberbu |  | 18.1% | 16.2% | 18.6% | 19.3% | 16.8% | 17.1% | 15.7% | 14.6% | 12.9% | 13.4% | 13.4% |
| Kakamega | Tiberbu | 8.3% | 13.3% | 47.4% | 25.0% | 15.5% | 17.2% | 24.0% | 16.0% | 16.2% | 14.7% | 14.5% | 14.0% |
| Bungoma | Tiberbu |  | 47.1% | 31.6% | 27.5% | 32.4% | 23.4% | 31.6% | 31.0% | 25.7% | 19.9% | 21.1% | 20.7% |
| Migori | Tiberbu | 63.6% | 30.8% | 30.9% | 40.8% | 38.4% | 44.7% | 46.0% | 37.4% | 28.8% | 27.8% | 27.3% | 26.3% |
| Kisumu | KenyaEMR | 22.2% | 21.4% | 24.2% | 20.1% | 18.6% | 16.4% | 21.0% | 20.5% | 19.3% | 9.6% | 11.4% | 11.6% |
| Turkana | Tiberbu |  | 0.0% | 36.4% | 9.5% | 38.8% | 41.9% | 20.2% | 24.5% | 34.5% | 27.5% | 27.4% | 25.8% |
| Busia | Tiberbu |  |  |  | 26.7% | 16.7% | 30.0% | 21.9% | 23.8% | 23.1% | 13.0% | 18.3% | 21.0% |
| Siaya | KenyaEMR | 5.9% | 16.3% | 22.7% | 26.4% | 31.9% | 19.3% | 26.2% | 21.7% | 17.4% | 11.1% | 8.7% | 8.6% |
| Nandi | Tiberbu | 6.2% | 3.9% | 13.8% | 1.6% | 2.5% | 2.0% | 3.3% | 4.7% | 3.4% | 2.2% | 2.5% | 2.6% |
| Kisii | Tiberbu |  |  |  |  |  | 22.2% | 5.3% | 8.9% | 7.8% | 8.6% | 8.0% | 6.7% |
| Mombasa | Tiberbu | 1.1% | 1.0% | 1.0% | 1.1% | 1.0% | 1.0% | 1.0% | 0.9% | 0.7% | 1.0% | 0.9% | 0.9% |
| Kericho | Tiberbu | 0.0% | 0.0% | 1.6% | 1.8% | 4.3% | 7.7% | 4.0% | 3.6% | 4.2% | 2.7% | 2.8% | 2.8% |
| Kilifi | KenyaEMR | 0.0% | 3.3% | 4.0% | 0.4% | 1.2% | 1.2% | 1.5% | 1.7% | 2.5% | 2.2% | 1.9% | 1.9% |
| Kwale | Tiberbu |  |  |  |  |  |  |  | 18.2% | 4.1% | 0.7% | 4.9% | 5.8% |
| Baringo | Tiberbu |  | 0.0% | 2.9% | 0.0% | 3.7% | 4.6% | 2.9% | 1.2% | 4.6% | 3.7% | 2.8% | 2.8% |

### Malaria tests

| County | Source | Nov 25 | Dec 25 | Jan 26 | Feb 26 | Mar 26 | Apr 26 | May 26 | Jun 26 | Jul 26 | Aug 26 | Sep 26 | Oct 26 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vihiga | Tiberbu |  | 130 | 4,472 | 8,933 | 10,826 | 10,534 | 13,002 | 9,491 | 9,293 | 3,305 | 8,305 | 10,613 |
| Kakamega | Tiberbu | 0 |  | 3 | 9 | 12 | 2 | 5 | 3 | 1,435 | 8,809 | 19,851 | 26,076 |
| Bungoma | Tiberbu |  | 2 | 14 | 6 | 9 | 7 | 10 | 5 | 409 | 2,282 | 17,419 | 27,310 |
| Migori | Tiberbu | 0 | 4 | 4 | 1 | 3 | 4 | 13 | 7 | 710 | 4,531 | 9,160 | 16,992 |
| Kisumu | KenyaEMR | 8,588 | 9,142 | 9,716 | 11,300 | 13,499 | 9,550 | 11,469 | 10,157 | 7,557 | 3,746 | 12,140 | 6,576 |
| Turkana | Tiberbu |  |  |  |  | 0 |  | 1 |  | 397 | 4,567 | 5,191 | 7,485 |
| Busia | Tiberbu |  |  |  | 4 | 2 | 0 | 1 | 2 | 66 | 221 | 3,872 | 11,967 |
| Siaya | KenyaEMR | 379 | 466 | 518 | 565 | 935 | 1,265 | 5,522 | 9,111 | 5,739 | 2,717 | 5,135 | 2,884 |
| Nandi | Tiberbu | 0 | 2 | 3 | 1 | 2 | 2 | 0 | 2 | 89 | 2,520 | 6,986 | 8,813 |
| Kisii | Tiberbu |  |  |  |  |  |  | 0 | 0 | 324 | 3,229 | 5,565 | 6,758 |
| Mombasa | Tiberbu | 3,748 | 2,215 | 1,691 | 3,951 | 3,185 | 4,045 | 5,580 | 4,202 | 2,976 | 1,082 | 4,192 | 8,304 |
| Kericho | Tiberbu | 3 | 2 | 4 | 3 | 4 | 6 | 4 | 11 | 48 | 527 | 4,750 | 5,923 |
| Kilifi | KenyaEMR | 4 | 15 | 79 | 63 | 146 | 373 | 703 | 3,567 | 5,940 | 5,942 | 8,056 | 4,056 |
| Kwale | Tiberbu |  |  |  |  |  |  |  | 0 | 16 | 12 | 3,289 | 8,574 |
| Baringo | Tiberbu |  | 1 | 5 | 6 | 5 | 4 | 6 | 9 | 129 | 949 | 1,855 | 3,308 |

### Malaria tests as a share of all tests

| County | Source | Nov 25 | Dec 25 | Jan 26 | Feb 26 | Mar 26 | Apr 26 | May 26 | Jun 26 | Jul 26 | Aug 26 | Sep 26 | Oct 26 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vihiga | Tiberbu |  | 43.5% | 48.6% | 57.9% | 61.7% | 57.0% | 57.6% | 58.2% | 50.4% | 43.3% | 48.7% | 49.5% |
| Kakamega | Tiberbu | 0.0% |  | 23.1% | 33.3% | 50.0% | 28.6% | 55.6% | 60.0% | 45.8% | 42.2% | 42.9% | 42.8% |
| Bungoma | Tiberbu |  | 66.7% | 48.3% | 40.0% | 47.4% | 30.4% | 30.3% | 17.9% | 52.8% | 48.8% | 41.3% | 39.8% |
| Migori | Tiberbu | 0.0% | 44.4% | 17.4% | 9.1% | 23.1% | 16.7% | 48.1% | 20.0% | 45.3% | 43.0% | 42.2% | 37.5% |
| Kisumu | KenyaEMR | 22.1% | 26.1% | 23.8% | 25.0% | 26.5% | 21.8% | 27.1% | 27.6% | 30.4% | 27.2% | 34.9% | 37.7% |
| Turkana | Tiberbu |  |  |  |  | 0.0% |  | 100.0% |  | 72.4% | 51.4% | 42.2% | 42.0% |
| Busia | Tiberbu |  |  |  | 80.0% | 100.0% | 0.0% | 100.0% | 40.0% | 57.9% | 40.6% | 43.5% | 45.5% |
| Siaya | KenyaEMR | 2.7% | 3.9% | 4.3% | 6.0% | 9.0% | 7.9% | 23.8% | 28.4% | 25.3% | 22.1% | 29.9% | 34.0% |
| Nandi | Tiberbu | 0.0% | 33.3% | 60.0% | 14.3% | 50.0% | 18.2% | 0.0% | 16.7% | 18.2% | 14.8% | 17.0% | 18.8% |
| Kisii | Tiberbu |  |  |  |  |  |  | 0.0% | 0.0% | 25.4% | 25.0% | 25.6% | 26.3% |
| Mombasa | Tiberbu | 18.5% | 15.2% | 12.0% | 17.7% | 19.8% | 21.4% | 26.0% | 23.6% | 19.1% | 14.3% | 20.2% | 18.4% |
| Kericho | Tiberbu | 21.4% | 11.1% | 13.3% | 11.5% | 10.8% | 18.8% | 10.5% | 15.1% | 18.7% | 14.3% | 14.0% | 14.1% |
| Kilifi | KenyaEMR | 0.1% | 1.2% | 1.9% | 1.3% | 3.8% | 7.6% | 8.7% | 18.3% | 20.5% | 19.5% | 17.6% | 20.8% |
| Kwale | Tiberbu |  |  |  |  |  |  |  | 0.0% | 8.4% | 6.2% | 19.8% | 22.1% |
| Baringo | Tiberbu |  | 7.7% | 10.2% | 10.2% | 16.7% | 11.1% | 12.5% | 18.0% | 21.0% | 16.3% | 13.9% | 15.2% |

Rates in months with only a handful of records, such as Kakamega before July 2026, are not meaningful.

## What this settles, and what is still open

Of the checks listed at the end of [03-malaria-data-map.md](03-malaria-data-map.md):

| Check | Answer |
|---|---|
| 1. Which codes mean malaria | Settled. Tiberbu: ICD-11 1F40 to 1F4Z and JB63.60. KenyaEMR and AMRS: concepts named malaria or plasmodium, less the HIV names. |
| 2. Which tests are malaria tests, and how a positive is written | Settled for names in all three sources and for results in KenyaEMR and AMRS. Tiberbu result values (`normal_test_result`) have not been read. |
| 3. Which drugs are antimalarials | Not done. |
| 4. Whether prescriptions can be tied to patients | Not done. |
| 5. Where KenyaEMR and AMRS diagnoses sit | Settled for malaria: `encounter_diagnosis` in both. AMRS has very few. |
| 6. Duplicates | Measured: 0.4% in Tiberbu diagnoses, 4% in KenyaEMR diagnoses and up to 16% in a month. |
| 7. Facility linkage for KenyaEMR | Open. County was taken from the default location as a stand-in. |
| 8. Volumes per source per month | Done, on this page. |

Still open for malaria:

- **Test positivity in Tiberbu**, which needs the result values.
- **Treatment**: antimalarials prescribed and dispensed.
- **Whether a diagnosis had a test behind it**, by linking diagnoses to tests on the same encounter. This would explain why Tiberbu has more diagnoses than tests.
- **How complete Tiberbu is before August 2026**, a question for the lake's owners.
- **Facility counts per county and month**, so that a rise can be split into more facilities and more cases.

## How the counts were made

- The queries are in `explorer/queries/malaria/`, one file per source and question, and can be run again with the `lake-explorer` tool. `explorer/scripts/malaria_summary.py` turns their output into the month-by-county tables and holds the rules for what counts as a malaria diagnosis or test.
- Voided rows (KenyaEMR, AMRS) and cancelled rows (Tiberbu) are left out. Repeated rows are removed by counting distinct record keys, except for the AMRS coded-answer and test-result counts, where the malaria rows showed no repeats.
- The KenyaEMR observation count lists the concept numbers inside the query. Joining the concept list to the 690 million observations ran out of memory three times on a 12 GB machine.
- County names are spelled differently in each source and were brought to one spelling. AMRS locations with no county in `facility_locations` use the location's own province field, and 77,365 AMRS test results have no county at all.
