-- Tiberbu structured forms: the fields inside each form submission and how often each is filled in.
-- A row of form_data_repository is one submitted form; its answers are a JSON object in observed_value.
-- Only the field names and counts are read here, never the answers.
WITH fields AS (
    SELECT form_name,
           unnest(map_entries(json_transform(
               CASE WHEN json_valid(observed_value) AND json_type(observed_value) = 'OBJECT'
                    THEN observed_value ELSE '{}' END,
               '"MAP(VARCHAR, VARCHAR)"'))) AS e
    FROM tiberbu.form_data_repository
    WHERE docstatus <> 2
)
SELECT form_name,
       e.key                                                                           AS field,
       count(*)                                                                        AS submissions,
       count(*) FILTER (WHERE e.value IS NOT NULL AND e.value NOT IN ('', '[]', '{}')) AS filled
FROM fields
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
