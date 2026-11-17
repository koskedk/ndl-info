-- KenyaEMR: all diagnoses and malaria diagnoses (encounter_diagnosis) by month and facility database,
-- from November 2025, dated by the encounter. Malaria = the coded diagnosis has a name mentioning malaria
-- or plasmodium, or the free-text diagnosis mentions them. The free text itself is not output. Totals only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'), min(name))     AS concept,
           bool_or(regexp_matches(lower(name), 'malaria|plasmod'))          AS mal
    FROM kenyaemr.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY 1
), d AS (
    SELECT source_schema, diagnosis_id, encounter_id, diagnosis_coded, date_created, certainty,
           diagnosis_coded IS NULL                                                        AS non_coded,
           regexp_matches(lower(coalesce(diagnosis_non_coded, '')), 'malaria|plasmod')    AS mal_text
    FROM kenyaemr.encounter_diagnosis
    WHERE CAST(voided AS INT) = 0 AND date_created >= TIMESTAMP '2025-10-01'
), e AS (
    SELECT source_schema, encounter_id, min(encounter_datetime) AS encounter_datetime
    FROM kenyaemr.encounter
    WHERE (source_schema, encounter_id) IN (SELECT (source_schema, encounter_id) FROM d)
    GROUP BY 1, 2
)
SELECT date_trunc('month', coalesce(e.encounter_datetime, d.date_created))::date AS month,
       d.source_schema,
       coalesce(n.mal, false) OR d.mal_text                       AS is_malaria,
       d.non_coded,
       CASE WHEN n.mal THEN d.diagnosis_coded END                 AS concept_id,
       CASE WHEN n.mal THEN n.concept END                         AS concept,
       CASE WHEN coalesce(n.mal, false) OR d.mal_text THEN d.certainty END AS certainty,
       count(*)                                                   AS loaded_rows,
       count(DISTINCT hash(d.source_schema, d.diagnosis_id))      AS diagnoses
FROM d
LEFT JOIN e ON e.source_schema = d.source_schema AND e.encounter_id = d.encounter_id
LEFT JOIN names n ON n.concept_id = d.diagnosis_coded
WHERE coalesce(e.encounter_datetime, d.date_created) >= TIMESTAMP '2025-11-01'
GROUP BY ALL
ORDER BY 1, 2;
