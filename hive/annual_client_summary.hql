USE ${hivevar:DATABASE};
SELECT client_id, substr(reading_date, 1, 4) AS year, COUNT(*) AS days,
       SUM(energy_kwh) AS energy_kwh, AVG(energy_kwh) AS mean_daily_kwh,
       MAX(energy_kwh) AS max_daily_kwh, MAX(peak_kw) AS peak_kw
FROM ${hivevar:TABLE}
GROUP BY client_id, substr(reading_date, 1, 4)
ORDER BY client_id, year;
