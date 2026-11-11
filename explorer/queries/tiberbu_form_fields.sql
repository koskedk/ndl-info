-- Tiberbu structured forms: the questions (fields) on each form and how often each is answered.
-- Field names only; no answers are read.
SELECT form_name,
       dictionary_concept          AS field,
       count(*)                    AS answers,
       count(DISTINCT patient)     AS patients,
       count(DISTINCT company)     AS facilities
FROM tiberbu.form_data_repository
WHERE docstatus <> 2
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
