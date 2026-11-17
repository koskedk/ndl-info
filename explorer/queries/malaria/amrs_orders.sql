-- AMRS: orders by month and location, from November 2025, with the county from facility_locations.
-- The ordered concept is kept only where its name could be a malaria test. Totals only.
WITH names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'), min(name)) AS concept,
           bool_or(regexp_matches(lower(name), 'malaria|plasmod|mrdt|\brdt\b|blood slide|smear|parasit|\bmps\b')) AS candidate
    FROM amrs.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY 1
), ot AS (
    SELECT order_type_id, min(name) AS order_type FROM amrs.order_type GROUP BY 1
), fl AS (
    SELECT location_id, min(county) AS county FROM amrs.facility_locations GROUP BY 1
), loc AS (
    SELECT location_id, min(name) AS location_name, min(state_province) AS state_province, min(county_district) AS county_district
    FROM amrs.location GROUP BY 1
), o AS (
    SELECT order_id, order_type_id, concept_id, encounter_id, date_activated, order_action
    FROM amrs.orders
    WHERE CAST(voided AS INT) = 0 AND date_activated >= TIMESTAMP '2025-11-01'
), e AS (
    SELECT encounter_id, min(location_id) AS location_id
    FROM amrs.encounter
    WHERE encounter_id IN (SELECT encounter_id FROM o)
    GROUP BY 1
)
SELECT date_trunc('month', o.date_activated)::date AS month,
       fl.county, loc.state_province, loc.county_district, e.location_id, loc.location_name,
       ot.order_type, o.order_action,
       CASE WHEN n.candidate THEN o.concept_id END AS concept_id,
       CASE WHEN n.candidate THEN n.concept END    AS concept,
       count(*)                                    AS loaded_rows,
       count(DISTINCT o.order_id)                  AS orders
FROM o
LEFT JOIN e   ON e.encounter_id = o.encounter_id
LEFT JOIN fl  ON fl.location_id = e.location_id
LEFT JOIN loc ON loc.location_id = e.location_id
LEFT JOIN ot  ON ot.order_type_id = o.order_type_id
LEFT JOIN names n ON n.concept_id = o.concept_id
GROUP BY ALL
ORDER BY 1, 2;
