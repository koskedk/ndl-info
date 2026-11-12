-- Tiberbu admissions by department: where maternity and newborn admissions sit.
SELECT medical_department,
       count(*)                                    AS admissions,
       count(DISTINCT company)                     AS facilities,
       count(*) FILTER (WHERE custom_is_deceased = 1) AS deaths,
       min(admitted_datetime)::date                AS first_admission,
       max(admitted_datetime)::date                AS last_admission
FROM tiberbu.inpatient_record
WHERE docstatus <> 2
GROUP BY 1
ORDER BY 2 DESC;
