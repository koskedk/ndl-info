-- KenyaEMR: orders by month and facility database from November 2025, read from the older copy
-- (hmis_kenya_emr), because the current copy's orders table holds only loads since 7 November 2026.
-- The older copy stops on 12 October 2026. The ordered concept is kept only where its name could be a
-- malaria test. Totals only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'), min(name)) AS concept,
           bool_or(regexp_matches(lower(name), 'malaria|plasmod|bs for mps|mps seen|\brdt\b|mrdt')) AS candidate
    FROM kenyaemr.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY 1
), o AS (
    SELECT date_trunc('month', date_activated)::date AS month, source_schema, order_type_id, order_action,
           concept_id, hash(source_schema, order_id) AS row_key
    FROM kenyaemr_old.orders
    WHERE CAST(voided AS INT) = 0 AND date_activated >= TIMESTAMP '2025-11-01' AND date_activated < TIMESTAMP '2026-12-01'
)
SELECT o.month, o.source_schema, o.order_type_id, o.order_action,
       CASE WHEN n.candidate THEN o.concept_id END AS concept_id,
       CASE WHEN n.candidate THEN n.concept END    AS concept,
       count(*)                  AS loaded_rows,
       count(DISTINCT o.row_key) AS orders
FROM o
LEFT JOIN names n ON n.concept_id = o.concept_id
GROUP BY ALL
ORDER BY 1, 2;
