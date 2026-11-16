-- KenyaEMR: activity per facility database over the last 12 months.
-- Totals per facility only. KenyaEMR carries no county, so the team places each database on the Master Facility List.
WITH types AS (
    SELECT source_schema, encounter_type_id, min(name) AS name FROM kenyaemr.encounter_type GROUP BY ALL
), e AS (
    SELECT e.source_schema, t.name, e.encounter_datetime
    FROM kenyaemr.encounter e
    JOIN types t ON t.source_schema = e.source_schema AND t.encounter_type_id = e.encounter_type
    WHERE NOT e.voided AND e.encounter_datetime >= DATE '2025-11-01'
)
SELECT source_schema,
       count(*) FILTER (WHERE name = 'ANC Mother Enrollment')                    AS anc_enrolments,
       count(*) FILTER (WHERE name = 'MCH Mother Consultation')                  AS anc_pnc_visits,
       count(*) FILTER (WHERE name IN ('MCH Partograph', 'MCH Inpatient'))       AS delivery,
       count(*) FILTER (WHERE name IN ('CWC Consultation', 'CWC Enrollment'))    AS child_clinic,
       count(*) FILTER (WHERE name IN ('Lab Order', 'Lab Results'))              AS lab,
       count(*)                                                                  AS all_encounters,
       count(DISTINCT date_trunc('month', encounter_datetime))                   AS months_active,
       max(encounter_datetime)::date                                             AS last_encounter
FROM e
GROUP BY ALL
HAVING anc_enrolments + anc_pnc_visits + delivery > 0
ORDER BY anc_enrolments + anc_pnc_visits + delivery DESC;
