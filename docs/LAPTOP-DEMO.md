# Laptop demo

The Python preparation and analytics run on Windows or Linux with Python 3.11+.
The project contains the extracted source under
`electricityloaddiagrams20112014/LD2011_2014.txt`.

```powershell
python -m pip install -r requirements.txt
python -m electricity prepare --input "electricityloaddiagrams20112014/LD2011_2014.txt" --output "data/prepared/electricity"
python -m electricity analyze --daily "data/prepared/electricity/daily.tsv" --output "results/electricity"
python -m electricity dashboard --results "results/electricity"
```

Preparation streams the 711 MB source and produces one row per client/day.
Allow time and disk space for the output. `analyze` runs the repository's
MapReduce mapper/reducer locally and checks their annual summaries against an
independent Python calculation.

The dashboard is read-only and requires a completed `analytics.json`. Page 1
looks up an ID such as `MT_001`, gives its annual Total kWh, Mean kWh/day, Max
daily kWh, and Peak kW for 2011–2014, then marks highest and lowest years by
annual Total kWh. The pie chart has a dropdown to select one metric (Total kWh,
Mean kWh/day, Max daily kWh, or Peak kW); slices show each year’s share of that
metric's sum across years. A bar chart compares annual total kWh. Page 2 takes a
year, ranking metric, and Top K (1–370), then highlights that metric’s highest
and lowest clients and displays the requested top K.

The pie chart compares only one selected metric at a time, so slices do not mix
kW and kWh-based measures. Stop the dashboard with Ctrl+C in the terminal.

MongoDB is optional:

```powershell
python -m electricity mongo --daily "data/prepared/electricity/daily.tsv" --database electricity_2011_2014
```

The Docker Hadoop containers are a separate Linux-oriented route. They must be
prepared with `scripts/install.sh`; see the three-system guide before using
HDFS, Pig, or Hive.
