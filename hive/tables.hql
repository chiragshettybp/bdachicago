CREATE DATABASE IF NOT EXISTS ${hivevar:DATABASE};
USE ${hivevar:DATABASE};
CREATE EXTERNAL TABLE IF NOT EXISTS daily_text (
    reading_date STRING, sr_type STRING, requests INT,
    completed INT, canceled INT, resolution_days DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '${hivevar:INPUT}';

CREATE EXTERNAL TABLE IF NOT EXISTS daily_rcfile (
    reading_date STRING, sr_type STRING, requests INT,
    completed INT, canceled INT, resolution_days DOUBLE
)
STORED AS RCFILE
LOCATION '${hivevar:RC_OUTPUT}';

SET hive.exec.compress.output=true;
SET mapred.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec;
SET mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.GzipCodec;
INSERT OVERWRITE TABLE daily_rcfile
SELECT reading_date, sr_type, requests, completed, canceled, resolution_days FROM daily_text;
ANALYZE TABLE daily_text COMPUTE STATISTICS;
ANALYZE TABLE daily_rcfile COMPUTE STATISTICS;
