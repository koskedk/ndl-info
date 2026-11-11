-- AMRS: which questions (concepts) are recorded in the maternal, child, family planning,
-- nutrition and death encounter types, and how often. Concept names only; no answers are read.
WITH enc AS (
    SELECT e.encounter_id, trim(t.name) AS encounter_type
    FROM amrs.encounter e
    JOIN amrs.encounter_type t ON t.encounter_type_id = e.encounter_type
    WHERE NOT e.voided
      AND trim(t.name) IN ('ANCADULTINITIAL', 'ANCADULTRETURN', 'PNCADULTINITIAL', 'PNCADULTRETURN',
                           'MNCHTRIAGE', 'MATERNITYADMISSION', 'MATERNITYDISCHARGE', 'LABORANDDELIVERY',
                           'LABORCAREGUIDE', 'IMMUNIZATIONVISIT', 'FPSCREENING', 'PEDSNUTRITION',
                           'HEIFOLLOWUP', 'NUTRITIONENCOUNTER', 'DEATHREPORT',
                           'PMTCTANC', 'PMTCTPOSTNATAL', 'ANCINITIAL', 'ANCRETURN', 'FAMILYPLANNING')
),
names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'),
                    min(name)) AS concept
    FROM amrs.concept_name
    WHERE NOT voided
    GROUP BY 1
),
counts AS (
    SELECT enc.encounter_type,
           o.concept_id,
           count(*)                                   AS obs,
           count(DISTINCT o.location_id)              AS locations,
           count(*) FILTER (WHERE o.value_coded IS NOT NULL)    AS coded,
           count(*) FILTER (WHERE o.value_numeric IS NOT NULL)  AS numeric,
           count(*) FILTER (WHERE o.value_datetime IS NOT NULL) AS dated,
           count(*) FILTER (WHERE o.value_text IS NOT NULL)     AS text
    FROM amrs.obs o
    JOIN enc ON enc.encounter_id = o.encounter_id
    WHERE NOT o.voided
    GROUP BY 1, 2
)
SELECT c.encounter_type, c.concept_id, n.concept, c.obs, c.locations, c.coded, c.numeric, c.dated, c.text
FROM counts c
LEFT JOIN names n ON n.concept_id = c.concept_id
ORDER BY 1, 4 DESC;
