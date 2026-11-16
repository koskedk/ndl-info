-- Tiberbu: programme enrolments per facility over the last 12 months.
-- Totals per facility only.
WITH e AS (
    SELECT company, county_id, program, name, date_enrolled
    FROM tiberbu.health_program_enrollment
    WHERE docstatus <> 2 AND date_enrolled >= DATE '2025-11-01'
)
SELECT company, min(county_id) AS county_id,
       count(DISTINCT name) FILTER (WHERE program = 'ANC')             AS anc,
       count(DISTINCT name) FILTER (WHERE program = 'PNC')             AS pnc,
       count(DISTINCT name) FILTER (WHERE program = 'Maternity Forms') AS maternity,
       count(DISTINCT name) FILTER (WHERE program = 'CWC')             AS child_clinic,
       count(DISTINCT date_trunc('month', date_enrolled))              AS months_active,
       max(date_enrolled)                                              AS last_enrolment
FROM e
GROUP BY ALL
HAVING anc + pnc + maternity > 0
ORDER BY anc + pnc + maternity DESC;
