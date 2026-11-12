-- Per-batch version of queries/tiberbu_form_fields.sql, for scripts/batched_count.py.
-- Field names and counts only; the answers are never written out.
WITH fields AS (
    SELECT form_name,
           unnest(map_entries(json_transform(
               CASE WHEN json_valid(observed_value) AND json_type(observed_value) = 'OBJECT'
                    THEN observed_value ELSE '{}' END,
               '"MAP(VARCHAR, VARCHAR)"'))) AS e
    FROM batch
    WHERE docstatus <> 2
)
SELECT form_name,
       e.key                                                                           AS field,
       count(*)                                                                        AS submissions,
       count(*) FILTER (WHERE e.value IS NOT NULL AND e.value NOT IN ('', '[]', '{}')) AS filled
FROM fields
GROUP BY 1, 2;
