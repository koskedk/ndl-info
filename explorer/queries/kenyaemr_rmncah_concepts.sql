-- KenyaEMR: which questions (concepts) are recorded in the maternal, child, family planning,
-- nutrition and mortality encounter types, and how often. Concept names only; no answers are read.
WITH types AS (
    SELECT source_schema, encounter_type_id, min(name) AS name
    FROM kenyaemr.encounter_type
    GROUP BY ALL
),
enc AS (
    SELECT e.source_schema, e.encounter_id, t.name AS encounter_type
    FROM kenyaemr.encounter e
    JOIN types t ON t.source_schema = e.source_schema AND t.encounter_type_id = e.encounter_type
    WHERE NOT e.voided
      AND t.name IN ('MCH Mother Consultation', 'MCH Mother Enrollment', 'ANC Mother Enrollment',
                     'PNC Mother Enrollment', 'MCH Mother Discontinuation', 'ANC Discontinuation',
                     'PNC Discontinuation', 'MCH Partograph', 'MCH Inpatient', 'New born admission',
                     'CWC Consultation', 'CWC Enrollment', 'Immunizations', 'MCH Child Immunization',
                     'MCH Child HEI Exit', 'MCH Child Discontinuation',
                     'Family Planning', 'Family Planning Enrollment', 'Family planning Discontinuation',
                     'Nutrition', 'Nutrition Enrollment', 'Nutrition Discontinuation', 'Mortality')
    GROUP BY ALL
),
names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'),
                    min(name)) AS concept
    FROM kenyaemr.concept_name
    WHERE NOT voided
    GROUP BY 1
),
counts AS (
    SELECT enc.encounter_type,
           o.concept_id,
           count(*)                                   AS obs,
           count(DISTINCT o.source_schema)            AS facilities,
           count(*) FILTER (WHERE o.value_coded IS NOT NULL)    AS coded,
           count(*) FILTER (WHERE o.value_numeric IS NOT NULL)  AS numeric,
           count(*) FILTER (WHERE o.value_datetime IS NOT NULL) AS dated,
           count(*) FILTER (WHERE o.value_text IS NOT NULL)     AS text
    FROM kenyaemr.obs o
    JOIN enc ON enc.source_schema = o.source_schema AND enc.encounter_id = o.encounter_id
    WHERE NOT o.voided
    GROUP BY 1, 2
)
SELECT c.encounter_type, c.concept_id, n.concept, c.obs, c.facilities, c.coded, c.numeric, c.dated, c.text
FROM counts c
LEFT JOIN names n ON n.concept_id = c.concept_id
ORDER BY 1, 4 DESC;
