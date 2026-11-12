-- KenyaEMR: the answer options recorded for the coded questions that RMNCAH-N indicators rest on
-- (vaccine given, place of birth, delivery attendant, birth outcome, family planning method, and so on).
-- Totals per answer option only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'),
                    min(name)) AS concept
    FROM kenyaemr.concept_name
    WHERE NOT voided
    GROUP BY 1
),
counts AS (
    SELECT concept_id,
           value_coded,
           count(*)                                                AS obs,
           count(DISTINCT source_schema)                           AS facilities,
           count(*) FILTER (WHERE obs_datetime >= DATE '2026-01-01') AS in_2026
    FROM kenyaemr.obs
    WHERE NOT voided
      AND value_coded IS NOT NULL
      AND concept_id IN (984,     -- immunizations (which vaccine)
                         1572,    -- location of birth
                         1573,    -- delivery assistant
                         5630,    -- method of delivery
                         159917,  -- qualitative birth outcome
                         159949,  -- quantitative outcome of delivery
                         160085,  -- maternal outcome
                         162134,  -- condition of newborn in postnatal period
                         374,     -- method of family planning
                         160653,  -- family planning status
                         5526,    -- breastfed exclusively
                         1151,    -- infant feeding method
                         161534,  -- vitamin A supplement
                         159922,  -- deworming
                         1591,    -- IPTp with SP
                         161004,  -- daily iron supplementation
                         159402,  -- malnutrition type
                         160205,  -- acute malnutrition
                         163304,  -- nutritional interventions provided
                         164464,  -- immunization status
                         161555)  -- reason for discontinuation of programme
    GROUP BY 1, 2
)
SELECT q.concept AS question, c.concept_id, a.concept AS answer, c.value_coded, c.obs, c.facilities, c.in_2026
FROM counts c
LEFT JOIN names q ON q.concept_id = c.concept_id
LEFT JOIN names a ON a.concept_id = c.value_coded
ORDER BY 1, 5 DESC;
