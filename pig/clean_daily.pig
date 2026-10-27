-- Preserve valid service request counts; reject malformed daily summaries.
raw = LOAD '$INPUT' USING PigStorage('\t') AS (
    reading_date:chararray, sr_type:chararray, requests:int,
    completed:int, canceled:int, resolution_days:double
);
clean = FILTER raw BY reading_date IS NOT NULL AND sr_type IS NOT NULL
    AND requests IS NOT NULL AND requests >= 0
    AND completed IS NOT NULL AND completed >= 0
    AND canceled IS NOT NULL AND canceled >= 0
    AND resolution_days IS NOT NULL AND resolution_days >= 0.0;
STORE clean INTO '$OUTPUT' USING PigStorage('\t');
