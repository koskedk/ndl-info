-- KenyaEMR encounters by type: volume, facilities and date range.
-- The encounter_type lookup holds repeated rows, so it is reduced to one name per id first.
WITH types AS (
    SELECT source_schema, encounter_type_id, min(name) AS name
    FROM kenyaemr.encounter_type
    GROUP BY ALL
)
SELECT t.name                                         AS encounter_type,
       count(*)                                       AS encounters,
       count(DISTINCT e.source_schema)                AS facilities,
       min(e.encounter_datetime)::date                AS first_date,
       max(e.encounter_datetime)::date                AS last_date,
       count(*) FILTER (WHERE year(e.encounter_datetime) = year(current_date)) AS this_year
FROM kenyaemr.encounter e
JOIN types t ON t.source_schema = e.source_schema AND t.encounter_type_id = e.encounter_type
WHERE NOT e.voided
GROUP BY 1
ORDER BY 2 DESC;
