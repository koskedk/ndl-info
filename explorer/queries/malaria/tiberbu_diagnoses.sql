-- Tiberbu: all diagnoses and malaria diagnoses by month and county, from November 2025.
-- A diagnosis counts as malaria if its description mentions malaria or plasmodium, or its code is an
-- ICD-10 malaria code (B50 to B54, P37.3, P37.4) or an ICD-11 one (1F40 to 1F45, 1F4Z).
-- Totals only. The code and description are kept for malaria rows so the matched values can be reviewed.
WITH d AS (
    SELECT date_trunc('month', creation)::date AS month,
           county_id,
           parenttype,
           (coalesce(description, '') || ' ' || coalesce(description_mapping, '')) ILIKE '%malaria%'
             OR (coalesce(description, '') || ' ' || coalesce(description_mapping, '')) ILIKE '%plasmodium%' AS by_keyword,
           regexp_matches(upper(coalesce(diagnosis_code, '') || ' ' || coalesce(entry_code, '')),
                          '(^|[^A-Z0-9])(B5[0-4]|P37\.?[34]|1F4[0-5Z])')                                   AS by_code,
           diagnosis_code, entry_code, description, suspected, confirmed_via,
           hash(name) AS row_key
    FROM tiberbu.diagnosis_entry
    WHERE docstatus <> 2 AND creation >= TIMESTAMP '2025-11-01'
)
SELECT month, county_id, parenttype,
       by_keyword OR by_code                                        AS is_malaria,
       by_keyword, by_code,
       CASE WHEN by_keyword OR by_code THEN diagnosis_code END      AS diagnosis_code,
       CASE WHEN by_keyword OR by_code THEN entry_code END          AS entry_code,
       CASE WHEN by_keyword OR by_code THEN description END         AS description,
       CASE WHEN by_keyword OR by_code THEN suspected END           AS suspected,
       CASE WHEN by_keyword OR by_code THEN confirmed_via END       AS confirmed_via,
       count(*)                                                     AS loaded_rows,
       count(DISTINCT row_key)                                      AS diagnoses
FROM d
GROUP BY ALL
ORDER BY 1, 2;
