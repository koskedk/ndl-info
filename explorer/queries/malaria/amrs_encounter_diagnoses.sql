-- AMRS: the small encounter_diagnosis table by month and location, with malaria flagged by the coded
-- diagnosis name or the free text (malaria or plasmodium). The free text itself is not output. Totals only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'), min(name)) AS concept,
           bool_or(regexp_matches(lower(name), 'malaria|plasmod')) AS mal
    FROM amrs.concept_name WHERE CAST(voided AS INT) = 0 GROUP BY 1
), d AS (
    SELECT diagnosis_id, encounter_id, diagnosis_coded, date_created,
           regexp_matches(lower(coalesce(diagnosis_non_coded, '')), 'malaria|plasmod') AS mal_text
    FROM amrs.encounter_diagnosis WHERE CAST(voided AS INT) = 0
), e AS (
    SELECT encounter_id, min(location_id) AS location_id, min(encounter_datetime) AS encounter_datetime
    FROM amrs.encounter WHERE encounter_id IN (SELECT encounter_id FROM d) GROUP BY 1
), fl AS (
    SELECT location_id, min(county) AS county FROM amrs.facility_locations GROUP BY 1
), loc AS (
    SELECT location_id, min(name) AS location_name, min(state_province) AS state_province FROM amrs.location GROUP BY 1
)
SELECT date_trunc('month', coalesce(e.encounter_datetime, d.date_created))::date AS month,
       fl.county, loc.state_province, e.location_id, loc.location_name,
       coalesce(n.mal, false) OR d.mal_text      AS is_malaria,
       CASE WHEN n.mal THEN n.concept END         AS concept,
       count(*)                                   AS loaded_rows,
       count(DISTINCT d.diagnosis_id)             AS diagnoses
FROM d
LEFT JOIN e ON e.encounter_id = d.encounter_id
LEFT JOIN fl ON fl.location_id = e.location_id
LEFT JOIN loc ON loc.location_id = e.location_id
LEFT JOIN names n ON n.concept_id = d.diagnosis_coded
GROUP BY ALL
ORDER BY 1, 2;
