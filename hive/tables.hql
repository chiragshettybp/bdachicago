CREATE DATABASE IF NOT EXISTS ${hivevar:DATABASE};
USE ${hivevar:DATABASE};
CREATE EXTERNAL TABLE IF NOT EXISTS daily_text (
    reading_date STRING, client_id STRING, intervals INT,
    energy_kwh DOUBLE, mean_kw DOUBLE, peak_kw DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '${hivevar:INPUT}';

CREATE EXTERNAL TABLE IF NOT EXISTS daily_rcfile (
    reading_date STRING, client_id STRING, intervals INT,
    energy_kwh DOUBLE, mean_kw DOUBLE, peak_kw DOUBLE
)
STORED AS RCFILE
LOCATION '${hivevar:RC_OUTPUT}';

SET hive.exec.compress.output=true;
SET mapred.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec;
SET mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.GzipCodec;
INSERT OVERWRITE TABLE daily_rcfile
SELECT reading_date, client_id, intervals, energy_kwh, mean_kw, peak_kw FROM daily_text;
ANALYZE TABLE daily_text COMPUTE STATISTICS;
ANALYZE TABLE daily_rcfile COMPUTE STATISTICS;
