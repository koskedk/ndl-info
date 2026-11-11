-- Tiberbu programme enrolments (ANC, CWC, family planning, and so on).
SELECT program,
       count(DISTINCT name)        AS enrolments,
       count(DISTINCT patient)     AS patients,
       count(DISTINCT company)     AS facilities,
       min(date_enrolled)          AS first_enrolment,
       max(date_enrolled)          AS last_enrolment
FROM tiberbu.health_program_enrollment
WHERE docstatus <> 2
GROUP BY 1
ORDER BY 2 DESC;
