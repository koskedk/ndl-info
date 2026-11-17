-- Tiberbu: lab tests ordered (lab_prescription) by month and county, from November 2025.
-- The test name is kept only for names that could be a malaria test, so they can be reviewed and classed
-- as rapid diagnostic test or microscopy afterwards. Totals only.
WITH p AS (
    SELECT date_trunc('month', creation)::date AS month,
           county_id,
           parenttype,
           lower(trim(regexp_replace(coalesce(lab_test_name, ''), '\s+', ' ', 'g'))) AS test_name,
           lower(coalesce(lab_test_code, ''))                                        AS test_code,
           hash(name) AS row_key
    FROM tiberbu.lab_prescription
    WHERE docstatus <> 2 AND creation >= TIMESTAMP '2025-11-01'
), c AS (
    SELECT *, regexp_matches(test_name || ' ' || test_code,
                             'malaria|mrdt|rdt|rapid diag|blood slide|smear|mps|plasmod|microscop|parasit|\bbs\b|b/s') AS candidate
    FROM p
)
SELECT month, county_id, parenttype, candidate,
       CASE WHEN candidate THEN test_name END AS test_name,
       CASE WHEN candidate THEN test_code END AS test_code,
       count(*)                AS loaded_rows,
       count(DISTINCT row_key) AS orders
FROM c
GROUP BY ALL
ORDER BY 1, 2;
