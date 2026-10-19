# Distributed Hadoop, Pig, and Hive run

This guide describes the distributed workflow for the electricity dataset.
The existing Docker/tool setup and shell scripts target Linux/Ubuntu; Windows
users can run preparation, local MapReduce validation, and the dashboard
natively, but should use Linux/WSL or three Linux machines for Hadoop/Pig/Hive.

## 1. Prepare tools and data

On the Linux master, install project tools once:

```bash
./scripts/install.sh
```

This fetches Java, Hadoop, Pig, and Hive into ignored `data/tools/` and pulls
the pinned images. It does not fetch the dataset. Prepare the checked-in data:

```bash
python3 -m electricity prepare \
  --input electricityloaddiagrams20112014/LD2011_2014.txt \
  --output data/prepared/electricity
```

## 2. Upload daily rows and run Hadoop Streaming

Start the configured HDFS/YARN cluster. Create a fresh HDFS run directory and
upload the daily data:

```bash
RUN=demo_001
ROOT=/user/$USER/electricity/$RUN
hdfs dfs -mkdir -p "$ROOT/input"
hdfs dfs -put data/prepared/electricity/daily.tsv "$ROOT/input/"
```

Run the annual client summary with a new output path:

```bash
scripts/run_mapreduce.sh "$ROOT/input" "$ROOT/mapreduce" 2
hdfs dfs -get "$ROOT/mapreduce" "results/$RUN-mapreduce"
```

The reducer emits client, year, day count, total kWh, mean daily kWh, maximum
daily kWh, and peak interval kW. The local `python -m electricity analyze`
command performs the same MapReduce calculation and checks it against the
reference summary.

## 3. Pig and Hive

Run Pig cleaning in MapReduce mode, preserving all valid zero readings:

```bash
pig -x mapreduce -param INPUT="$ROOT/input" -param OUTPUT="$ROOT/clean" \
  -f pig/clean_daily.pig
```

Use `hive/tables.hql` to create Text and RCFile tables, setting `INPUT` to the
Pig-cleaned HDFS path and `RC_OUTPUT` to a new HDFS path. Then run
`hive/annual_client_summary.hql` twice with `TABLE=daily_text` and
`TABLE=daily_rcfile`; confirm the aggregates agree. Keep the output locations
unique for each run.

## Interpretation and limitations

- kWh is computed as `kW / 4` for each supplied 15-minute reading.
- A missing/blank value is an error; a numeric zero is retained.
- Client columns that represent clients added later are kept as explicit zeros
  for earlier records, as provided by the dataset.
- Portugal DST rules are represented in the source's values, not reconstructed.
  Avoid claiming that 1:00–2:00 is directly comparable on DST transition days.
- Three Docker containers on one host are not the same as three physical
  computers. Record actual cluster topology separately for coursework evidence.
