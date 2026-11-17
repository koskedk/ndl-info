-- Tiberbu: lab tests done (lab_test) by month and county, from November 2025.
-- The test name is kept only for names that could be a malaria test. Totals only.
WITH t AS (
    SELECT date_trunc('month', CAST(date AS TIMESTAMP))::date AS month,
           county_id,
           status,
           lower(trim(regexp_replace(coalesce(nullif(trim(template), ''), lab_test_name, ''), '\s+', ' ', 'g'))) AS test_name,
           hash(name) AS row_key
    FROM tiberbu.lab_test
    WHERE docstatus <> 2 AND CAST(date AS TIMESTAMP) >= TIMESTAMP '2025-11-01'
), c AS (
    SELECT *, regexp_matches(test_name,
                             'malaria|mrdt|rdt|rapid diag|blood slide|smear|mps|plasmod|microscop|parasit|\bbs\b|b/s') AS candidate
    FROM t
)
SELECT month, county_id, status, candidate,
       CASE WHEN candidate THEN test_name END AS test_name,
       count(*)                AS loaded_rows,
       count(DISTINCT row_key) AS tests
FROM c
GROUP BY ALL
ORDER BY 1, 2;
