-- KHIS indicators in the lake: months covered and facilities reporting.
SELECT api_name                    AS indicator,
       count(*)                    AS facility_months,
       count(DISTINCT facility_id) AS facilities,
       min(period_id)              AS first_month,
       max(period_id)              AS last_month
FROM khis.data
GROUP BY 1
ORDER BY 1;
