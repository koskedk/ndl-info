-- Tiberbu vital signs: how many readings carry the child-growth measures.
SELECT count(*)                                                                  AS readings,
       count(DISTINCT company)                                                   AS facilities,
       count(*) FILTER (WHERE weight > 0)                                        AS with_weight,
       count(*) FILTER (WHERE height > 0)                                        AS with_height,
       count(*) FILTER (WHERE custom_muac IS NOT NULL AND custom_muac NOT IN ('', '0'))       AS with_muac,
       count(DISTINCT company) FILTER (WHERE custom_muac IS NOT NULL AND custom_muac NOT IN ('', '0')) AS muac_facilities,
       count(*) FILTER (WHERE custom_z_score IS NOT NULL AND custom_z_score NOT IN ('', '0')) AS with_z_score,
       count(*) FILTER (WHERE custom_head_circumference > 0)                     AS with_head_circumference
FROM tiberbu.vital_signs
WHERE docstatus <> 2;
