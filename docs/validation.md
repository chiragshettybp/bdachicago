# Validation record

The automated suite includes small generated data fixtures for preparation,
zero retention, annual aggregation, local MapReduce agreement, malformed input,
client ID lookup, client-year rankings, missing-client handling, invalid-year
handling, and the saved-results dashboard.

The client dashboard identifies highest and lowest years by annual total kWh.
The selected-year view ranks clients by total kWh and breaks ties consistently
by client ID. The client pie chart lets the user choose one annual measure at a
time (Total kWh, Mean kWh/day, Max daily kWh, or Peak kW) and compares its
yearly shares; it does not combine unrelated kWh and kW measurements into one
pie. The year ranking also selects a measure and Top K.

For a full-data validation, retain the generated `manifest.json` and
`analytics.json`. The manifest records the source SHA-256, interval and
client-row counts, date coverage, conversion, and timestamp handling.

The Hadoop Streaming, Pig, Hive, and MongoDB paths require their services to be
available and are not considered passed merely because the local tests pass.
Record each real execution and the machine topology separately.
