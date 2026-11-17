-- KenyaEMR: concepts whose name suggests malaria, a malaria test, or a diagnosis question.
-- Dictionary entries only; no patient data is read.
WITH n AS (
    SELECT concept_id, name, count(DISTINCT source_schema) AS facilities
    FROM kenyaemr.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY ALL
)
SELECT CASE WHEN regexp_matches(lower(name), 'malaria|plasmod|mrdt|\brdt\b|blood slide|smear|parasit|\bmps\b')
            THEN 'malaria' ELSE 'diagnosis question' END AS kind,
       concept_id, name, facilities
FROM n
WHERE regexp_matches(lower(name), 'malaria|plasmod|mrdt|\brdt\b|blood slide|smear|parasit|\bmps\b|diagnos|problem added|problem list')
ORDER BY 1 DESC, 2, 3;
