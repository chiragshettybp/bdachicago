# Technical reference

## Commands

```text
python -m electricity prepare --input SOURCE --output NEW_DIRECTORY
python -m electricity analyze --daily PREPARED/daily.tsv --output NEW_DIRECTORY
python -m electricity mongo --daily PREPARED/daily.tsv --database electricity_NAME
python -m electricity dashboard --results RESULTS_DIRECTORY
```

Output directories must not already exist; this prevents accidental mixing of
runs. Download the UCI dataset and place `LD2011_2014.txt` at
`electricityloaddiagrams20112014/LD2011_2014.txt`. Preparation produces
`daily.tsv` and `manifest.json`. Analysis produces `analytics.json` and
`mapreduce.tsv`.

## Daily TSV schema

Headerless, tab-separated columns:

```text
date  client_id  intervals  energy_kwh  mean_kw  peak_kw
```

There are 96 rows per day/client, including explicit zero values. Time stamps
are interpreted as interval ends; readings at midnight are included in the
previous day. `energy_kwh` is calculated from the quarter-hour kW values.

## MongoDB

The optional importer uses `MONGODB_URI`, defaulting to
`mongodb://127.0.0.1:27017`. It refuses non-empty destination databases.
Choose a new `electricity_<name>` database for each import.

## Hadoop tools

The large source dataset and generated `data/`/`results/` are ignored by Git.
`data/tools/` is local setup output. `infra/prepare_tools.py`
retrieves verified Hadoop, Pig, Hive, and Java distributions. The distributed
cluster files remain under `infra/`; the dataset-specific scripts and schemas
are under `mapreduce/`, `pig/`, and `hive/`.
