-- Tiberbu structured forms: how many records, patients and facilities each form has.
SELECT form_name,
       count(DISTINCT name)        AS records,
       count(DISTINCT patient)     AS patients,
       count(DISTINCT company)     AS facilities,
       min(creation)::date         AS first_record,
       max(creation)::date         AS last_record
FROM tiberbu.form_data_repository
WHERE docstatus <> 2
GROUP BY 1
ORDER BY 3 DESC;
