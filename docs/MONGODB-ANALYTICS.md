# MongoDB analytics

The existing `python -m electricity mongo` workflow ingests the prepared daily
TSV into MongoDB, creates the `client_year` and `date` indexes, and calculates
annual client summaries with an aggregation pipeline. This separate profiling
command is read-only: it reports the collection's document count and indexes,
runs `explain` with execution statistics for a client lookup and annual
aggregation, and saves the annual aggregation results as JSON.

Start MongoDB and import the prepared data first. For example, from the
repository root in PowerShell:

```powershell
python -m electricity mongo --daily "data/prepared/electricity/daily.tsv" --database electricity_2011_2014
```

Then generate the report for a client:

```powershell
python -m electricity.mongo_profile --database electricity_2011_2014 --client-id MT_001 --output "results/mongodb-analytics.json"
```

Open `results/mongodb-analytics.json` to show the document count, index
definitions, query and aggregation execution statistics, and per-year results.
The report includes the number of documents and index keys examined and the
execution time reported by MongoDB. Execution times can vary between runs, so
use the examined-document and examined-key counts alongside the milliseconds
when discussing query performance.

The database must already contain the importer's `daily_readings` collection.
The report command does not modify or replace imported data.
