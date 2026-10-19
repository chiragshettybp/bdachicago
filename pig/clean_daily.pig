-- Preserve valid zero-load readings; reject malformed daily summaries.
raw = LOAD '$INPUT' USING PigStorage('\t') AS (
    reading_date:chararray, client_id:chararray, intervals:int,
    energy_kwh:double, mean_kw:double, peak_kw:double
);
clean = FILTER raw BY reading_date IS NOT NULL AND client_id IS NOT NULL
    AND intervals == 96 AND energy_kwh IS NOT NULL AND energy_kwh >= 0.0
    AND mean_kw IS NOT NULL AND mean_kw >= 0.0
    AND peak_kw IS NOT NULL AND peak_kw >= 0.0;
STORE clean INTO '$OUTPUT' USING PigStorage('\t');
