-- Tiberbu: maternal and newborn death notices per facility.
-- Totals per facility only. Used to make sure the sample includes hospitals that record deaths.
SELECT hospital_of_demise, facility_kmhfl_code, min(facility_county) AS facility_county, min(facility_level) AS facility_level,
       count(*) FILTER (WHERE notification_type ILIKE '%maternal%')                                         AS maternal_deaths,
       count(*) FILTER (WHERE notification_type ILIKE '%neonat%' OR notification_type ILIKE '%perinat%')    AS newborn_deaths,
       count(*)                                                                                             AS all_death_notices,
       min(date_of_death) AS first_death, max(date_of_death) AS last_death
FROM tiberbu.death_notification
WHERE docstatus <> 2
GROUP BY ALL
HAVING maternal_deaths + newborn_deaths > 0
ORDER BY maternal_deaths DESC, newborn_deaths DESC;
