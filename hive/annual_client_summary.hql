USE ${hivevar:DATABASE};
SELECT sr_type, substr(reading_date, 1, 4) AS year, COUNT(*) AS days,
       SUM(requests) AS requests, AVG(requests) AS mean_daily_requests,
       MAX(requests) AS max_daily_requests,
       SUM(resolution_days) / NULLIF(SUM(completed), 0) AS avg_resolution_days
FROM ${hivevar:TABLE}
GROUP BY sr_type, substr(reading_date, 1, 4)
ORDER BY sr_type, year;
