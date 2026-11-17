-- KenyaEMR: the county of each facility database, read from the facility's own default location.
-- KenyaEMR tables carry no county column. Facility attributes only; no patient data is read.
WITH gp AS (
    SELECT source_schema, max(property_value) AS location_id
    FROM kenyaemr.global_property
    WHERE property = 'kenyaemr' || '.defaultLocation'
    GROUP BY 1
)
SELECT gp.source_schema, gp.location_id,
       min(l.name)            AS facility_name,
       min(l.county_district) AS county_district,
       min(l.state_province)  AS state_province,
       min(l.address4)        AS address4,
       min(l.address5)        AS address5,
       min(l.address6)        AS address6,
       min(l.city_village)    AS city_village
FROM gp
LEFT JOIN kenyaemr.location l
       ON l.source_schema = gp.source_schema AND CAST(l.location_id AS VARCHAR) = gp.location_id
GROUP BY 1, 2
ORDER BY 1;
