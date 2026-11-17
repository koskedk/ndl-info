-- AMRS: concepts whose name suggests malaria, a malaria test, or a diagnosis question,
-- plus concepts mapped to an ICD-10 malaria code (B50 to B54, P37.3, P37.4).
-- Dictionary entries only; no patient data is read.
WITH n AS (
    SELECT concept_id, name
    FROM amrs.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY ALL
), icd AS (
    SELECT m.concept_id, s.name AS source, t.code, t.name AS term_name
    FROM amrs.concept_reference_map m
    JOIN amrs.concept_reference_term t ON t.concept_reference_term_id = m.concept_reference_term_id
    JOIN amrs.concept_reference_source s ON s.concept_source_id = t.concept_source_id
    WHERE regexp_matches(upper(t.code), '^(B5[0-4]|P37\.?[34])') AND s.name ILIKE '%icd%'
    GROUP BY ALL
)
SELECT CASE WHEN regexp_matches(lower(name), 'malaria|plasmod|mrdt|\brdt\b|blood slide|smear|parasit|\bmps\b')
            THEN 'malaria' ELSE 'diagnosis question' END AS kind,
       concept_id, name, '' AS icd_source, '' AS icd_code
FROM n
WHERE regexp_matches(lower(name), 'malaria|plasmod|mrdt|\brdt\b|blood slide|smear|parasit|\bmps\b|diagnos|problem added|problem list')
UNION ALL
SELECT 'icd-10 malaria code', icd.concept_id, coalesce(min(n.name), min(icd.term_name)), icd.source, icd.code
FROM icd LEFT JOIN n USING (concept_id)
GROUP BY icd.concept_id, icd.source, icd.code
ORDER BY 1 DESC, 2, 3;
