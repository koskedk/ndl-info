-- KenyaEMR: order type names. Dictionary entries only.
SELECT order_type_id, name, java_class_name, count(DISTINCT source_schema) AS facilities
FROM kenyaemr.order_type GROUP BY ALL ORDER BY 1, 4 DESC;
