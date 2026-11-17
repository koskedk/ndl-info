-- AMRS: observations from November 2025 that are a coded answer, a result tied to an order, a test-class
-- concept, or recorded against a malaria concept; by month and location. One pass over obs gives:
--   * diagnoses recorded as coded answers (malaria and all), by the question they were recorded under
--   * malaria test results (rapid test, blood smear) and all test results
-- q_class and a_class are the concept class numbers of the question and of the coded answer.
-- The question is kept only where it is a diagnosis question, a malaria concept, or has malaria among its
-- answers; other questions are added together. Totals only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'), min(name)) AS concept,
           bool_or(regexp_matches(lower(name), 'malaria|plasmod|bs for mps|mps seen'))
             AND NOT bool_or(lower(name) LIKE '%without mention of%')  AS mal,
           bool_or(regexp_matches(lower(name), 'diagnos|problem added|problem list')) AS dx_q
    FROM amrs.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY 1
), mal AS (
    SELECT concept_id FROM names WHERE mal
), cls AS (
    SELECT concept_id, min(class_id) AS class_id FROM amrs.concept GROUP BY 1
), s AS (
    SELECT date_trunc('month', b.obs_datetime)::date AS month,
           b.location_id,
           b.concept_id,
           cq.class_id AS q_class,
           ca.class_id AS a_class,
           CASE WHEN mq.concept_id IS NOT NULL OR mv.concept_id IS NOT NULL THEN b.value_coded END AS value_coded,
           mv.concept_id IS NOT NULL AS malaria_answer,
           b.order_id IS NOT NULL    AS has_order,
           CASE WHEN mq.concept_id IS NOT NULL OR mv.concept_id IS NOT NULL THEN b.obs_id END AS malaria_key,
           b.order_id                AS order_key
    FROM amrs.obs b
    LEFT JOIN mal mq ON mq.concept_id = b.concept_id
    LEFT JOIN mal mv ON mv.concept_id = b.value_coded
    LEFT JOIN cls cq ON cq.concept_id = b.concept_id
    LEFT JOIN cls ca ON ca.concept_id = b.value_coded
    WHERE CAST(b.voided AS INT) = 0
      AND b.obs_datetime >= TIMESTAMP '2025-11-01' AND b.obs_datetime < TIMESTAMP '2026-12-01'
      AND (b.value_coded IS NOT NULL OR b.order_id IS NOT NULL OR mq.concept_id IS NOT NULL OR cq.class_id IN (1, 8))
), o AS MATERIALIZED (
    SELECT month, location_id, concept_id, q_class, a_class, value_coded, malaria_answer, has_order,
           grouping(concept_id)        AS is_total,
           count(*)                    AS loaded_rows,
           count(DISTINCT malaria_key) AS malaria_rows,
           count(DISTINCT order_key)   AS orders
    FROM s
    GROUP BY GROUPING SETS ((month, location_id, concept_id, q_class, a_class, value_coded, malaria_answer, has_order),
                            (month, location_id, has_order))
), keep AS (
    SELECT concept_id FROM o WHERE malaria_answer AND is_total = 0
    UNION
    SELECT concept_id FROM names WHERE mal OR dx_q
), fl AS (
    SELECT location_id, min(county) AS county FROM amrs.facility_locations GROUP BY 1
), loc AS (
    SELECT location_id, min(name) AS location_name, min(state_province) AS state_province, min(county_district) AS county_district
    FROM amrs.location GROUP BY 1
)
SELECT o.month, fl.county, loc.state_province, loc.county_district, o.location_id, loc.location_name,
       o.is_total, o.has_order, o.q_class, o.a_class,
       CASE WHEN k.concept_id IS NOT NULL THEN o.concept_id END AS concept_id,
       CASE WHEN k.concept_id IS NOT NULL THEN n.concept END    AS concept,
       o.value_coded,
       vn.concept                                               AS value_name,
       o.malaria_answer,
       sum(o.loaded_rows)  AS loaded_rows,
       sum(o.malaria_rows) AS malaria_rows,
       sum(o.orders)       AS orders
FROM o
LEFT JOIN keep k   ON k.concept_id = o.concept_id
LEFT JOIN names n  ON n.concept_id = o.concept_id
LEFT JOIN names vn ON vn.concept_id = o.value_coded
LEFT JOIN fl       ON fl.location_id = o.location_id
LEFT JOIN loc      ON loc.location_id = o.location_id
GROUP BY ALL
ORDER BY 1, 2;
