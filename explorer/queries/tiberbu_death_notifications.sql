-- Tiberbu death notifications by type and period of death, as totals.
-- The audited count is reliable; the pregnancy and stillborn flags depend on answer wording not yet checked.
SELECT notification_type,
       period_of_death,
       count(*)                                              AS notifications,
       count(DISTINCT facility_kmhfl_code)                   AS facilities,
       count(*) FILTER (WHERE death_audited = 1)             AS audited,
       count(*) FILTER (WHERE deceased_pregnant NOT IN ('', 'No') AND deceased_pregnant IS NOT NULL) AS pregnancy_related,
       count(*) FILTER (WHERE stillborn NOT IN ('', 'No', '0') AND stillborn IS NOT NULL)            AS stillborn_flag,
       count(*) FILTER (WHERE age_at_death_days BETWEEN 0 AND 28 AND baby_outcome IS NOT NULL AND baby_outcome <> '') AS with_baby_outcome,
       min(date_of_death)                                    AS first_death,
       max(date_of_death)                                    AS last_death
FROM tiberbu.death_notification
WHERE docstatus <> 2
GROUP BY 1, 2
ORDER BY 3 DESC;
