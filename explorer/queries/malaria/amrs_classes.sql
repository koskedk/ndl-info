-- AMRS: how many concepts fall in each concept class, with three example names per class, so the
-- class numbers can be read (the lake has no concept_class table for AMRS). Dictionary entries only.
WITH n AS (
    SELECT concept_id, min(name) AS name FROM amrs.concept_name
    WHERE CAST(voided AS INT) = 0 AND concept_name_type = 'FULLY_SPECIFIED' GROUP BY 1
), c AS (
    SELECT concept_id, min(class_id) AS class_id FROM amrs.concept GROUP BY 1
)
SELECT c.class_id, count(*) AS concepts,
       max(CASE WHEN c.concept_id IN (32, 123, 847, 9187, 6042, 1284) THEN c.concept_id || ' ' || n.name END) AS known_example,
       min(n.name) AS example_1, max(n.name) AS example_2
FROM c LEFT JOIN n USING (concept_id)
GROUP BY 1 ORDER BY 1;
