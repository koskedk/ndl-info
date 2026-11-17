-- KenyaEMR: observations from November 2025 that are a coded answer, a result tied to an order, or
-- recorded against a malaria concept; by month and facility database. One pass over obs gives:
--   * diagnoses recorded as coded answers (malaria and all), by the question they were recorded under
--   * malaria test results (rapid test, blood smear) and all results tied to an order
-- The question is kept only where it is a diagnosis question or a malaria concept, or the answer is a
-- malaria concept; other questions are added together. Totals only.
--
-- The concept numbers are written into the query (taken from out/malaria/kenyaemr_concepts.csv: names
-- matching malaria or plasmodium, and names of diagnosis questions) instead of being joined in. Three
-- earlier versions that joined the concept list to obs ran out of memory.
-- Repeated rows are removed exactly (distinct_rows) for malaria rows only; loaded_rows may include repeats.
WITH s AS (
    SELECT date_trunc('month', obs_datetime)::date AS month,
           source_schema,
           CASE WHEN is_mal_q OR is_mal_v OR is_dx_q THEN concept_id END AS concept_id,
           CASE WHEN is_mal_q OR is_mal_v THEN value_coded END           AS value_coded,
           is_mal_v                  AS malaria_answer,
           value_coded IS NOT NULL   AS is_coded,
           order_id IS NOT NULL      AS has_order,
           CASE WHEN is_mal_q OR is_mal_v THEN hash(source_schema, obs_id) END AS malaria_key
    FROM (
        SELECT obs_datetime, source_schema, concept_id, value_coded, order_id, obs_id,
               concept_id IN (32, 33, 34, 35, 123, 189, 364, 397, 847, 906, 1366, 1476, 1558, 1643, 1908, 1909, 1913, 5839, 5840, 115898, 116125, 116127, 116128, 117627, 118353, 123008, 124925, 126490, 127971, 129936, 131096, 131377, 134041, 134592, 134594, 135359, 135360, 135361, 137565, 138283, 139197, 143850, 145851, 149132, 152295, 152296, 155686, 158379, 159519, 159610, 159950, 160148, 160149, 160150, 160151, 160152, 160153, 160154, 160155, 161246, 161247, 161248, 161426, 161465, 162686, 162754, 164485, 164884, 166623, 166703, 167850, 168740, 168986, 168987, 168988, 168989, 168990, 168991, 168992, 169035, 2001193, 2002436, 2002437, 2002438, 2002439, 2002440, 2002441, 2002443, 2002444, 2002446, 2002631, 2002634, 2002636, 2002637, 2002639, 2002641, 2002642, 2002644, 2002646, 2002649, 2002650, 2002652, 2010297, 2017901, 2017917, 2017936, 2018002, 2018021, 2018035, 2018052, 2018087, 2018114, 2018122, 2025817, 2025819, 2025820, 2031151, 2031852, 2032282, 2032283, 2032284, 2032285, 2032286, 2032287, 2032290, 2032291, 2032295, 2032334, 2032335, 2032336, 2032337, 2032341, 2032982, 2032983) AS is_mal_q,
               coalesce(value_coded IN (32, 33, 34, 35, 123, 189, 364, 397, 847, 906, 1366, 1476, 1558, 1643, 1908, 1909, 1913, 5839, 5840, 115898, 116125, 116127, 116128, 117627, 118353, 123008, 124925, 126490, 127971, 129936, 131096, 131377, 134041, 134592, 134594, 135359, 135360, 135361, 137565, 138283, 139197, 143850, 145851, 149132, 152295, 152296, 155686, 158379, 159519, 159610, 159950, 160148, 160149, 160150, 160151, 160152, 160153, 160154, 160155, 161246, 161247, 161248, 161426, 161465, 162686, 162754, 164485, 164884, 166623, 166703, 167850, 168740, 168986, 168987, 168988, 168989, 168990, 168991, 168992, 169035, 2001193, 2002436, 2002437, 2002438, 2002439, 2002440, 2002441, 2002443, 2002444, 2002446, 2002631, 2002634, 2002636, 2002637, 2002639, 2002641, 2002642, 2002644, 2002646, 2002649, 2002650, 2002652, 2010297, 2017901, 2017917, 2017936, 2018002, 2018021, 2018035, 2018052, 2018087, 2018114, 2018122, 2025817, 2025819, 2025820, 2031151, 2031852, 2032282, 2032283, 2032284, 2032285, 2032286, 2032287, 2032290, 2032291, 2032295, 2032334, 2032335, 2032336, 2032337, 2032341, 2032982, 2032983), false) AS is_mal_v,
               concept_id IN (1284, 1459, 1476, 1497, 1642, 1661, 1687, 1815, 1908, 1913, 6042, 6097, 83852, 85203, 113919, 117189, 126224, 126231, 128339, 129860, 129875, 130719, 133010, 133012, 133013, 133014, 133015, 133016, 133943, 136785, 138975, 141397, 142729, 142730, 142731, 142732, 142733, 148052, 148053, 148054, 148055, 148056, 150852, 150854, 151990, 151991, 154434, 154435, 154436, 158390, 159392, 159393, 159394, 159396, 159546, 159550, 159551, 159565, 159946, 159947, 159948, 159977, 160167, 160168, 160169, 160170, 160171, 160172, 160173, 160174, 160175, 160176, 160177, 160178, 160179, 160180, 160181, 160182, 160212, 160213, 160249, 160250, 160526, 160554, 160567, 160592, 160617, 161194, 161204, 161251, 161254, 161356, 161357, 161378, 161465, 161602, 161828, 162166, 162334, 162984, 163034, 163035, 163414, 163716, 163752, 163767, 163772, 163898, 163970, 164083, 164084, 164113, 164159, 164383, 164391, 164398, 164418, 164500, 164537, 164594, 164663, 164851, 165039, 165479, 165562, 165794, 165852, 165860, 165909, 165910, 166200, 166208, 167431, 167432, 167434, 167789, 168137, 168549, 169173, 169217, 1000144, 1000223, 1000444, 1000516, 1000518, 2000985, 2008505, 2009595, 2009596, 2009597, 2009629, 2009630, 2009631, 2009632, 2009633, 2009634, 2009636, 2009637, 2009658, 2009700, 2009826, 2009827, 2009906, 2009907, 2009940, 2009941, 2009942, 2010213, 2010223, 2010224, 2010225, 2010283, 2012582, 2012592, 2012595, 2012597, 2012599, 2012608, 2012610, 2012874, 2012882, 2012931, 2012933, 2012934, 2013031, 2013039, 2013057, 2013263, 2013265, 2013319, 2013341, 2013359, 2013420, 2013480, 2013683, 2013718, 2015084, 2015085, 2015090, 2022908, 2026706, 2026843, 2029297, 2029298, 2029302, 2029306, 2029311, 2029312, 2029313, 2029314, 2029315, 2029317, 2029318, 2029319, 2029320, 2029547, 2029550, 2031533, 2031534, 2032072, 2032073, 2032108, 2032776, 2032777, 2033637, 2033769) AS is_dx_q
        FROM kenyaemr.obs
        WHERE CAST(voided AS INT) = 0
          AND obs_datetime >= TIMESTAMP '2025-11-01' AND obs_datetime < TIMESTAMP '2026-12-01'
    )
    WHERE value_coded IS NOT NULL OR order_id IS NOT NULL OR is_mal_q
), o AS MATERIALIZED (
    SELECT month, source_schema, concept_id, value_coded, malaria_answer, is_coded, has_order,
           count(*)                    AS loaded_rows,
           count(DISTINCT malaria_key) AS distinct_rows
    FROM s
    GROUP BY ALL
), names AS (
    SELECT concept_id,
           coalesce(min(name) FILTER (WHERE locale = 'en' AND concept_name_type = 'FULLY_SPECIFIED'),
                    min(name) FILTER (WHERE locale = 'en'), min(name)) AS concept
    FROM kenyaemr.concept_name
    WHERE CAST(voided AS INT) = 0
    GROUP BY 1
)
SELECT o.month, o.source_schema, o.has_order, o.is_coded, o.concept_id, n.concept,
       o.value_coded, vn.concept AS value_name, o.malaria_answer, o.loaded_rows, o.distinct_rows
FROM o
LEFT JOIN names n  ON n.concept_id = o.concept_id
LEFT JOIN names vn ON vn.concept_id = o.value_coded
ORDER BY 1, 2;
