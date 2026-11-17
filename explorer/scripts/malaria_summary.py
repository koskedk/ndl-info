"""Turn the malaria query outputs in out/malaria/ into month-by-county tables.

Reads the totals written by the queries in queries/malaria/ (no lake access, no patient rows)
and writes result_*.csv next to them. Run from the explorer folder:

    uv run --offline python scripts/malaria_summary.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

OUT = Path("out/malaria")
FIRST, LAST = "2025-11-01", "2026-10-01"   # the twelve complete months reported

con = duckdb.connect()


def have(name: str) -> bool:
    return (OUT / f"{name}.csv").is_file()


def view(name: str, types: dict[str, str] | None = None) -> None:
    cast = f", types={types}" if types else ""
    con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv('{OUT / (name + '.csv')}'{cast})")


def save(name: str, sql: str) -> None:
    con.execute(f"COPY ({sql}) TO '{OUT / (name + '.csv')}' (HEADER)")
    rows = con.execute(f"SELECT count(*) FROM read_csv('{OUT / (name + '.csv')}')").fetchone()[0]
    print(f"  wrote {name}.csv ({rows:,} rows)")


# How a test name is classed. Names were reviewed from the lake on 17 November 2026.
TEST_KIND = """
    CASE
      WHEN regexp_matches(n, 'mps/mrdt')                                             THEN 'malaria test, method not stated'
      WHEN regexp_matches(n, 'mrdt|malaria r(dt|apid)|rapid malaria|\\(rdt\\)- malaria|rapid test for malaria|rapid diagnostic test kit for malaria') THEN 'rapid diagnostic test'
      WHEN regexp_matches(n, 'malaria (bs|blood smear|microscopy|smear|sm,)|blood slide for malaria|blood smear for (malaria )?parasites|bs for mps|malarial smear|malarial parasites|^b/s$') THEN 'microscopy'
      WHEN regexp_matches(n, 'malaria pcr')                                           THEN 'other malaria test'
    END
"""

TESTS_PART = """
        SELECT '{source}' AS source, '{stage}' AS stage, month, county, sum(n) AS all_tests,
               coalesce(sum(n) FILTER (WHERE kind IS NOT NULL), 0)                AS malaria_tests,
               coalesce(sum(n) FILTER (WHERE kind = 'rapid diagnostic test'), 0)  AS rapid_tests,
               coalesce(sum(n) FILTER (WHERE kind = 'microscopy'), 0)             AS microscopy,
               coalesce(sum(n) FILTER (WHERE kind NOT IN ('rapid diagnostic test', 'microscopy')), 0) AS other_malaria_tests
        FROM {view} GROUP BY ALL"""

parts_dx: list[str] = []
parts_tests: list[str] = []

# ---------------------------------------------------------------- Tiberbu
if have("tiberbu_diagnoses"):
    print("Tiberbu diagnoses")
    view("tiberbu_diagnoses", {"diagnosis_code": "VARCHAR", "entry_code": "VARCHAR", "suspected": "VARCHAR",
                                "confirmed_via": "VARCHAR", "description": "VARCHAR"})
    # 'Tested for Malaria' is a laboratory-examination entry (QA00.C), not a diagnosis of malaria.
    con.execute("""
        CREATE OR REPLACE VIEW t_dx AS
        SELECT month, replace(county_id, '_', ' ') AS county, diagnoses,
               is_malaria AND coalesce(description, '') <> 'Tested for Malaria' AS malaria,
               by_code, by_keyword, diagnosis_code, description, suspected
        FROM tiberbu_diagnoses""")
    parts_dx.append("""
        SELECT 'Tiberbu' AS source, 'diagnosis entries' AS recorded_as, month, county,
               sum(diagnoses) AS all_diagnoses, coalesce(sum(diagnoses) FILTER (WHERE malaria), 0) AS malaria_diagnoses
        FROM t_dx GROUP BY ALL""")
    save("result_tiberbu_malaria_diagnosis_values", f"""
        SELECT trim(regexp_extract(diagnosis_code, '^[A-Z0-9.]+')) AS code,
               trim(regexp_replace(diagnosis_code, '^[A-Z0-9.]+\\s*-\\s*', '')) AS code_title,
               coalesce(description, '(none)') AS reporting_group,
               CASE WHEN by_code THEN 'ICD-11 malaria code' ELSE 'keyword only' END AS matched_on,
               malaria AS counted_as_malaria,
               sum(diagnoses) AS diagnoses
        FROM t_dx WHERE (by_code OR by_keyword) AND month BETWEEN '{FIRST}' AND '{LAST}'
        GROUP BY ALL ORDER BY diagnoses DESC""")

for stage, name, measure in (("ordered", "tiberbu_lab_orders", "orders"), ("done", "tiberbu_lab_tests", "tests")):
    if not have(name):
        continue
    print(f"Tiberbu tests {stage}")
    view(name, {"test_name": "VARCHAR"})
    con.execute(f"""
        CREATE OR REPLACE VIEW t_{stage} AS
        SELECT month, replace(county_id, '_', ' ') AS county, {measure} AS n, test_name, ({TEST_KIND}) AS kind
        FROM (SELECT *, coalesce(test_name, '') AS n FROM {name})""")
    parts_tests.append(TESTS_PART.format(source="Tiberbu", stage=f"tests {stage}", view=f"t_{stage}"))
    save(f"result_tiberbu_test_names_{stage}", f"""
        SELECT test_name, classed_as, sum(n) AS tests
        FROM (SELECT test_name, coalesce(kind, 'not a malaria test') AS classed_as, n, month FROM t_{stage})
        WHERE test_name IS NOT NULL AND month BETWEEN '{FIRST}' AND '{LAST}'
        GROUP BY test_name, classed_as ORDER BY (classed_as = 'not a malaria test'), tests DESC""")

# County names are written differently in each source; bring them to one spelling.
con.execute("""
    CREATE OR REPLACE MACRO county_name(c) AS
    CASE trim(regexp_replace(lower(coalesce(c, '')), '[/_\\-\\s]+', ' ', 'g'))
         WHEN ''           THEN 'unknown'
         WHEN 'transnzoia' THEN 'trans nzoia'
         WHEN 'sirisia'    THEN 'bungoma'
         WHEN 'test'       THEN 'unknown'
         ELSE trim(regexp_replace(lower(c), '[/_\\-\\s]+', ' ', 'g'))
    END""")

# ---------------------------------------------------------------- KenyaEMR
if have("kenyaemr_county"):
    view("kenyaemr_county")
    con.execute("""CREATE OR REPLACE VIEW k_county AS
                   SELECT source_schema, county_name(county_district) AS county FROM kenyaemr_county""")

# Names that mention malaria but are not a diagnosis of malaria.
NOT_MALARIA = "without mention of|^h/o|smear, qualitative|before the seizure"
HIV_WITH_MALARIA = "hiv disease|human immunodeficiency"

if have("kenyaemr_diagnoses") and have("kenyaemr_county"):
    print("KenyaEMR diagnoses (encounter_diagnosis)")
    view("kenyaemr_diagnoses", {"concept": "VARCHAR", "certainty": "VARCHAR"})
    con.execute(f"""
        CREATE OR REPLACE VIEW k_dx AS
        SELECT d.month, coalesce(c.county, 'unknown') AS county, d.diagnoses, d.concept, d.concept_id,
               CASE WHEN NOT d.is_malaria THEN 'not malaria'
                    WHEN d.concept IS NULL THEN 'malaria (free text)'
                    WHEN regexp_matches(lower(d.concept), '{NOT_MALARIA}') THEN 'not malaria (name only mentions it)'
                    WHEN regexp_matches(lower(d.concept), '{HIV_WITH_MALARIA}') THEN 'HIV disease associated with malaria'
                    ELSE 'malaria' END AS class
        FROM kenyaemr_diagnoses d LEFT JOIN k_county c USING (source_schema)""")
    parts_dx.append("""
        SELECT 'KenyaEMR' AS source, 'diagnosis entries' AS recorded_as, month, county,
               sum(diagnoses) AS all_diagnoses,
               coalesce(sum(diagnoses) FILTER (WHERE class IN ('malaria', 'malaria (free text)')), 0) AS malaria_diagnoses
        FROM k_dx GROUP BY ALL""")
    save("result_kenyaemr_malaria_diagnosis_values", f"""
        SELECT concept_id, coalesce(concept, '(free text mentioning malaria)') AS diagnosis, class AS counted_as, sum(diagnoses) AS diagnoses
        FROM k_dx WHERE class <> 'not malaria' AND month BETWEEN '{FIRST}' AND '{LAST}'
        GROUP BY ALL ORDER BY diagnoses DESC""")

if have("kenyaemr_old_orders") and have("kenyaemr_county"):
    print("KenyaEMR tests ordered (older copy, to 12 October 2026)")
    view("kenyaemr_old_orders", {"concept": "VARCHAR"})
    # Order type 3 is the test order. A DISCONTINUE row is written when a result is entered, so only NEW rows are orders.
    con.execute(f"""
        CREATE OR REPLACE VIEW k_ordered AS
        SELECT o.month, coalesce(c.county, 'unknown') AS county, o.orders AS n, o.concept AS test_name, ({TEST_KIND}) AS kind
        FROM (SELECT *, lower(coalesce(concept, '')) AS n FROM kenyaemr_old_orders
              WHERE order_type_id = 3 AND order_action = 'NEW') o
        LEFT JOIN k_county c USING (source_schema)""")
    parts_tests.append(TESTS_PART.format(source="KenyaEMR", stage="tests ordered", view="k_ordered"))

if have("kenyaemr_obs") and have("kenyaemr_county"):
    print("KenyaEMR malaria test results (obs)")
    view("kenyaemr_obs", {"concept": "VARCHAR", "value_name": "VARCHAR"})
    # 2017901 'Malaria Parasites' is the result line of a blood smear (2017917 is its panel heading and the
    # species and staging lines belong to the same smear, so they are not counted again). 32 is the older
    # smear concept used on forms. 1643 is the rapid test. 2032282 is malaria PCR.
    # Observations tied to an order rise from about 180,000 a month to 1.9 million in October 2026 while
    # test orders do not, so they are not used as an all-tests total. Rates for KenyaEMR come from orders.
    con.execute("""
        CREATE OR REPLACE VIEW k_results AS
        SELECT b.month, coalesce(c.county, 'unknown') AS county, b.distinct_rows AS n,
               CASE WHEN b.concept_id IN (2017901, 32, 1366) THEN 'microscopy'
                    WHEN b.concept_id = 1643 THEN 'rapid diagnostic test'
                    ELSE 'other malaria test' END AS kind,
               coalesce(b.value_name, '') IN ('MPS Seen', 'Positive', 'DETECTED', 'THREE PLUS') AS positive
        FROM kenyaemr_obs b LEFT JOIN k_county c USING (source_schema)
        WHERE b.concept_id IN (2017901, 32, 1366, 1643, 2032282)""")
    parts_tests.append("""
        SELECT 'KenyaEMR' AS source, 'malaria test results recorded' AS stage, month, county, NULL AS all_tests,
               sum(n) AS malaria_tests,
               coalesce(sum(n) FILTER (WHERE kind = 'rapid diagnostic test'), 0) AS rapid_tests,
               coalesce(sum(n) FILTER (WHERE kind = 'microscopy'), 0)            AS microscopy,
               coalesce(sum(n) FILTER (WHERE kind = 'other malaria test'), 0)    AS other_malaria_tests
        FROM k_results GROUP BY ALL""")
    save("result_kenyaemr_malaria_test_results", f"""
        SELECT month, county,
               coalesce(sum(n) FILTER (WHERE kind = 'microscopy'), 0)                         AS smear_results,
               coalesce(sum(n) FILTER (WHERE kind = 'microscopy' AND positive), 0)            AS smear_positive,
               coalesce(sum(n) FILTER (WHERE kind = 'rapid diagnostic test'), 0)              AS rapid_results,
               coalesce(sum(n) FILTER (WHERE kind = 'rapid diagnostic test' AND positive), 0) AS rapid_positive
        FROM k_results WHERE month BETWEEN '{FIRST}' AND '{LAST}' GROUP BY ALL ORDER BY 1, 2""")

# ---------------------------------------------------------------- AMRS
AMRS_COUNTY = "county_name(coalesce(county, state_province))"

if have("amrs_encounter_diagnoses"):
    print("AMRS diagnoses (encounter_diagnosis)")
    view("amrs_encounter_diagnoses", {"concept": "VARCHAR", "county": "VARCHAR", "state_province": "VARCHAR"})
    parts_dx.append(f"""
        SELECT 'AMRS' AS source, 'diagnosis entries' AS recorded_as, month, {AMRS_COUNTY} AS county,
               sum(diagnoses) AS all_diagnoses,
               coalesce(sum(diagnoses) FILTER (WHERE is_malaria AND NOT regexp_matches(lower(coalesce(concept, '')),
                                                     '{NOT_MALARIA}|{HIV_WITH_MALARIA}')), 0) AS malaria_diagnoses
        FROM amrs_encounter_diagnoses GROUP BY ALL""")

if have("amrs_obs"):
    print("AMRS coded observations and test results")
    view("amrs_obs", {"concept": "VARCHAR", "value_name": "VARCHAR", "county": "VARCHAR", "state_province": "VARCHAR"})
    # Diagnosis questions in use: 6042 problem added, 1929 admission diagnosis, 11679 problem list (coded),
    # 8568 discharge diagnosis, 11647 visit diagnosis, 1284 problem list.
    parts_dx.append(f"""
        SELECT 'AMRS' AS source, 'coded observations' AS recorded_as, month, {AMRS_COUNTY} AS county,
               sum(loaded_rows) AS all_diagnoses, coalesce(sum(loaded_rows) FILTER (WHERE malaria_answer), 0) AS malaria_diagnoses
        FROM amrs_obs WHERE is_total = 0 AND concept_id IN (6042, 1929, 11679, 8568, 11647, 1284) GROUP BY ALL""")
    # Concept class 1 is the test class in AMRS.
    con.execute(f"""
        CREATE OR REPLACE VIEW a_results AS
        SELECT month, {AMRS_COUNTY} AS county, loaded_rows AS n, concept AS test_name, ({TEST_KIND}) AS kind
        FROM (SELECT *, lower(coalesce(concept, '')) AS n FROM amrs_obs WHERE is_total = 0 AND q_class = 1)""")
    parts_tests.append(TESTS_PART.format(source="AMRS", stage="test results recorded", view="a_results"))

if have("amrs_orders"):
    print("AMRS tests ordered")
    view("amrs_orders", {"concept": "VARCHAR", "county": "VARCHAR", "state_province": "VARCHAR", "county_district": "VARCHAR"})
    con.execute(f"""
        CREATE OR REPLACE VIEW a_ordered AS
        SELECT month, {AMRS_COUNTY} AS county, orders AS n, concept AS test_name, ({TEST_KIND}) AS kind
        FROM (SELECT *, lower(coalesce(concept, '')) AS n FROM amrs_orders WHERE order_type = 'Test' AND order_action = 'NEW')""")
    parts_tests.append(TESTS_PART.format(source="AMRS", stage="tests ordered", view="a_ordered"))

# ---------------------------------------------------------------- combined outputs
if parts_dx:
    save("result_diagnoses_by_month_county", f"""
        SELECT *, round(100.0 * malaria_diagnoses / nullif(all_diagnoses, 0), 2) AS malaria_pct
        FROM ({' UNION ALL '.join(parts_dx)})
        WHERE month BETWEEN '{FIRST}' AND '{LAST}' ORDER BY source, recorded_as, month, county""")
if parts_tests:
    save("result_tests_by_month_county", f"""
        SELECT *, round(100.0 * malaria_tests / nullif(all_tests, 0), 2) AS malaria_pct
        FROM ({' UNION ALL '.join(parts_tests)})
        WHERE month BETWEEN '{FIRST}' AND '{LAST}' ORDER BY source, stage, month, county""")

# ---------------------------------------------------------------- county-by-month layouts, for reading
def pivot(name: str, source_file: str, group: str, value: str) -> None:
    months = [r[0] for r in con.execute(
        f"SELECT DISTINCT strftime(month, '%Y-%m') FROM read_csv('{OUT / source_file}') ORDER BY 1").fetchall()]
    cols = ", ".join(f"max(CASE WHEN strftime(month, '%Y-%m') = '{m}' THEN {value} END) AS \"{m}\"" for m in months)
    save(name, f"""SELECT source, {group}, county, {cols}
                   FROM read_csv('{OUT / source_file}') GROUP BY ALL ORDER BY 1, 2, 3""")


if parts_dx:
    pivot("result_pivot_malaria_diagnoses", "result_diagnoses_by_month_county.csv", "recorded_as", "malaria_diagnoses")
    pivot("result_pivot_malaria_diagnosis_pct", "result_diagnoses_by_month_county.csv", "recorded_as", "malaria_pct")
if parts_tests:
    pivot("result_pivot_malaria_tests", "result_tests_by_month_county.csv", "stage", "malaria_tests")
    pivot("result_pivot_malaria_test_pct", "result_tests_by_month_county.csv", "stage", "malaria_pct")
