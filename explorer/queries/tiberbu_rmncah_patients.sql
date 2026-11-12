-- Tiberbu patients: how many are flagged as newborns, linked to a mother, or linked to a childbirth record.
SELECT count(*)                                                                  AS patients,
       count(*) FILTER (WHERE custom_newborn = 1)                                AS newborn_flag,
       count(*) FILTER (WHERE custom_parent IS NOT NULL AND custom_parent <> '') AS linked_to_parent,
       count(*) FILTER (WHERE custom_childbirth_record IS NOT NULL AND custom_childbirth_record <> '') AS linked_to_childbirth,
       count(*) FILTER (WHERE dob IS NULL)                                       AS no_dob,
       count(*) FILTER (WHERE dob > current_date - INTERVAL 5 YEAR)              AS under_5,
       count(*) FILTER (WHERE sex = 'Female' AND dob BETWEEN current_date - INTERVAL 20 YEAR AND current_date - INTERVAL 10 YEAR) AS girls_10_19,
       count(*) FILTER (WHERE sex = 'Female' AND dob BETWEEN current_date - INTERVAL 50 YEAR AND current_date - INTERVAL 15 YEAR) AS women_15_49
FROM tiberbu.patient
WHERE docstatus <> 2;
