-- AMRS: activity per location over the last 12 months, with the county from facility_locations.
-- Totals per facility only. Used to choose the POC facilities, starting from where AMRS is.
WITH types AS (
    SELECT encounter_type_id, trim(min(name)) AS name FROM amrs.encounter_type GROUP BY ALL
), fl AS (
    SELECT location_id, min(facility_name) AS facility_name, min(county) AS county, min(sub_county) AS sub_county,
           min(facility_level) AS facility_level, min(facility_owner) AS facility_owner
    FROM amrs.facility_locations GROUP BY ALL
), e AS (
    SELECT e.location_id, t.name, e.encounter_datetime
    FROM amrs.encounter e
    LEFT JOIN types t ON t.encounter_type_id = e.encounter_type
    WHERE NOT e.voided AND e.encounter_datetime >= DATE '2025-11-01'
)
SELECT fl.county, fl.sub_county, fl.facility_name, fl.facility_level, fl.facility_owner, e.location_id,
       count(*) FILTER (WHERE name IN ('ANCINITIAL', 'ANCRETURN', 'ANCADULTINITIAL', 'ANCADULTRETURN', 'PMTCTANC')) AS anc,
       count(*) FILTER (WHERE name IN ('PNCADULTINITIAL', 'PNCADULTRETURN', 'POSTNATAL', 'PMTCTPOSTNATAL'))        AS pnc,
       count(*) FILTER (WHERE name IN ('LABORANDDELIVERY', 'MATERNITYADMISSION', 'MATERNITYDISCHARGE', 'LABORCAREGUIDE')) AS delivery,
       count(*) FILTER (WHERE name IN ('LABORDERENCOUNTER', 'POCLAB', 'Lab Results', 'Lab Order'))                 AS lab,
       count(*)                                                    AS all_encounters,
       count(DISTINCT date_trunc('month', encounter_datetime))     AS months_active,
       max(encounter_datetime)::date                               AS last_encounter
FROM e
LEFT JOIN fl USING (location_id)
GROUP BY ALL
HAVING anc + pnc + delivery > 0
ORDER BY anc + pnc + delivery DESC;
