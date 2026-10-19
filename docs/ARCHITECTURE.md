# Architecture

## Dataset

The source is UCI ElectricityLoadDiagrams20112014, a semicolon-separated file
with 370 client columns and 140,256 interval rows. A value is power in kW for a
15-minute interval. Each interval's energy is therefore `kW / 4` kWh.

The timestamp marks the end of its interval. Preparation assigns readings to
the date of the interval start (`timestamp - 15 minutes`), so the midnight
boundary readings remain within their preceding day. Daily records are checked
to contain 96 observations per client. Zeroes remain explicit; they are not
treated as null or removed.

## Processing flow

```text
LD2011_2014.txt
  -> electricity.prepare: validate rows and stream to daily.tsv
  -> Python reference aggregation + Hadoop Streaming cross-check
  -> optional MongoDB daily collection and annual aggregation
  -> Pig validation/cleaning -> Hive Text and RCFile tables
  -> saved JSON/TSV results -> Flask dashboard
```

The normalized TSV has six columns:

| Column | Meaning |
|---|---|
| `date` | Date assigned to the 15-minute intervals ending on that date |
| `client_id` | UCI client identifier, e.g. `MT_001` |
| `intervals` | Expected to be 96 |
| `energy_kwh` | Daily sum of interval kW readings divided by four |
| `mean_kw` | Average interval power for the day |
| `peak_kw` | Maximum recorded 15-minute power |

The main report groups by client and year. It contains number of days, total
kWh, mean daily kWh, maximum daily kWh, and peak interval kW. MapReduce computes
the same annual summary from daily rows; the local workflow compares the two
before saving results.

## Dashboard pages

Page 1 looks up one client by ID and displays its available annual metrics for
2011–2014. A dropdown selects Total kWh, Mean kWh/day, Max daily kWh, or Peak
kW as the pie basis. Slices show each year’s share of the selected metric's sum
across available years, while a bar chart compares annual total kWh and
highlights highest/lowest consumption years. Page 2 takes a calendar year, a
ranking metric, and Top K (1–370); it highlights the metric's maximum and
minimum clients and displays the top K in sorted order. The pie compares one
measure at a time instead of mixing energy and power units.

## Distributed tools

- **HDFS** stores the normalized TSV across the cluster.
- **YARN and Hadoop Streaming** execute the Python mapper and reducer.
- **Pig** validates the daily schema and retains valid zero-load readings.
- **Hive** queries the same daily rows in Text and RCFile formats.
- **MongoDB** is an optional separate persistence and aggregation path.
- **Flask** reads completed local analytics; it does not start data jobs.

Portuguese-time daylight-saving handling is kept exactly as supplied. The
spring transition contains zero values and the autumn transition aggregates
two hours into the 1:00–2:00 labels. Annual and daily sums use the supplied
values; time-of-day comparisons around these transitions require care.
