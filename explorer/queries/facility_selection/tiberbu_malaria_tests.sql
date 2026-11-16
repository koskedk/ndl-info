-- Tiberbu: which lab tests are malaria tests, and how many each facility ran over the last 12 months.
-- Test names and totals only.
WITH t AS (
    SELECT company, county_id, coalesce(nullif(trim(template), ''), lab_test_name) AS test_name, date
    FROM tiberbu.lab_test
    WHERE docstatus <> 2 AND date >= DATE '2025-11-01'
      AND (template ILIKE '%malaria%' OR lab_test_name ILIKE '%malaria%'
           OR template ILIKE '%mrdt%' OR lab_test_name ILIKE '%mrdt%'
           OR template ILIKE '%blood slide%' OR lab_test_name ILIKE '%blood slide%'
           OR template ILIKE '%bs for mps%' OR lab_test_name ILIKE '%bs for mps%'
           OR template ILIKE '%plasmodium%' OR lab_test_name ILIKE '%plasmodium%')
)
SELECT 'test name' AS part, test_name AS item, '' AS county_id, count(*) AS tests, count(DISTINCT company) AS facilities
FROM t GROUP BY ALL
UNION ALL
SELECT 'facility', company, min(county_id), count(*), 1
FROM t GROUP BY company
ORDER BY 1 DESC, 4 DESC;
