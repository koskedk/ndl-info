-- AMRS encounters by type: volume, locations and date range.
SELECT t.name                                         AS encounter_type,
       count(*)                                       AS encounters,
       count(DISTINCT e.location_id)                  AS locations,
       min(e.encounter_datetime)::date                AS first_date,
       max(e.encounter_datetime)::date                AS last_date,
       count(*) FILTER (WHERE year(e.encounter_datetime) = year(current_date)) AS this_year
FROM amrs.encounter e
LEFT JOIN amrs.encounter_type t ON t.encounter_type_id = e.encounter_type
WHERE NOT e.voided
GROUP BY 1
ORDER BY 2 DESC;
