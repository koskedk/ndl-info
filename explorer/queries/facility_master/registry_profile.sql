-- Facility registry: how many facilities, which identifiers are filled, and what each code looks like.
-- Totals and code shapes only (digits shown as 9, letters as A). No facility or person details.
WITH r AS (
  SELECT fidCode, frCode, registrationNumber, uuid, kephLevel, facilityOwnership,
         internal_ingestion_timestamp, internal_sync_run_id
  FROM facility.facility_registry
), shape AS (
  SELECT 'fidCode' AS col, regexp_replace(regexp_replace(fidCode, '[0-9]', '9', 'g'), '[A-Za-z]', 'A', 'g') AS shape, count(DISTINCT fidCode) AS n FROM r GROUP BY ALL
  UNION ALL
  SELECT 'frCode', regexp_replace(regexp_replace(frCode, '[0-9]', '9', 'g'), '[A-Za-z]', 'A', 'g'), count(DISTINCT frCode) FROM r GROUP BY ALL
  UNION ALL
  SELECT 'registrationNumber', regexp_replace(regexp_replace(registrationNumber, '[0-9]', '9', 'g'), '[A-Za-z]', 'A', 'g'), count(DISTINCT registrationNumber) FROM r GROUP BY ALL
)
SELECT '1 totals' AS part, 'rows' AS item, cast(count(*) AS varchar) AS value FROM r
UNION ALL SELECT '1 totals', 'distinct fidCode', cast(count(DISTINCT fidCode) AS varchar) FROM r
UNION ALL SELECT '1 totals', 'distinct frCode', cast(count(DISTINCT frCode) AS varchar) FROM r
UNION ALL SELECT '1 totals', 'distinct registrationNumber', cast(count(DISTINCT registrationNumber) AS varchar) FROM r
UNION ALL SELECT '1 totals', 'distinct uuid', cast(count(DISTINCT uuid) AS varchar) FROM r
UNION ALL SELECT '1 totals', 'rows with no fidCode', cast(count(*) FILTER (WHERE coalesce(trim(fidCode), '') = '') AS varchar) FROM r
UNION ALL SELECT '1 totals', 'rows with no frCode', cast(count(*) FILTER (WHERE coalesce(trim(frCode), '') = '') AS varchar) FROM r
UNION ALL SELECT '1 totals', 'sync runs', cast(count(DISTINCT internal_sync_run_id) AS varchar) FROM r
UNION ALL SELECT '1 totals', 'first ingestion', min(internal_ingestion_timestamp) FROM r
UNION ALL SELECT '1 totals', 'last ingestion', max(internal_ingestion_timestamp) FROM r
UNION ALL SELECT '1 totals', 'frCode values per fidCode (max)', cast(max(c) AS varchar) FROM (SELECT count(DISTINCT frCode) c FROM r WHERE coalesce(trim(fidCode), '') <> '' GROUP BY fidCode)
UNION ALL SELECT '1 totals', 'fidCode values per frCode (max)', cast(max(c) AS varchar) FROM (SELECT count(DISTINCT fidCode) c FROM r WHERE coalesce(trim(frCode), '') <> '' GROUP BY frCode)
UNION ALL SELECT '2 shape ' || col, coalesce(shape, '(empty)'), cast(n AS varchar) FROM (SELECT *, row_number() OVER (PARTITION BY col ORDER BY n DESC) rn FROM shape) WHERE rn <= 4
UNION ALL SELECT '3 kephLevel', coalesce(kephLevel, '(empty)'), cast(count(DISTINCT fidCode) AS varchar) FROM r GROUP BY ALL
UNION ALL SELECT '4 ownership', coalesce(facilityOwnership, '(empty)'), cast(count(DISTINCT fidCode) AS varchar) FROM r GROUP BY ALL
ORDER BY 1, 3 DESC;
