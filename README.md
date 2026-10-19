# Electricity Load Analytics

Big Data Analytics project using the UCI [ElectricityLoadDiagrams20112014
dataset](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014).
It contains 370 client columns with 15-minute power readings from 2011 through
2014.

The project validates the wide source file, converts it to daily energy records,
and compares annual per-client summaries using Python, MongoDB, Hadoop
MapReduce, Pig, and Hive. A two-page Flask dashboard lets users inspect a
client's four-year profile or rank clients by a selected year.

## Energy interpretation

- Source values are kW; each interval represents 15 minutes, so interval energy
  in kWh is `kW / 4`.
- Every daily record contains all 96 intervals. Zero readings are data, not
  missing values; zero-filled periods before a client appears are retained.
- Timestamps label interval ends. A midnight timestamp is assigned to the
  preceding day, preserving the dataset's 96 records per day.
- The original Portuguese-time daylight-saving conventions are preserved.
  Spring-transition zeroes and autumn-transition aggregated consumption make
  time-of-day comparisons around those dates special cases.

## Quick start (Python, Windows or Linux)

Use Python 3.11 or newer. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Download the dataset from [UCI](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014)
and place its `LD2011_2014.txt` file at
`electricityloaddiagrams20112014/LD2011_2014.txt`. (The supplied local copy is
already in that location.) Then produce annual summaries:

```powershell
python -m electricity prepare --input "electricityloaddiagrams20112014/LD2011_2014.txt" --output "data/prepared/electricity"
python -m electricity analyze --daily "data/prepared/electricity/daily.tsv" --output "results/electricity"
python -m electricity dashboard --results "results/electricity"
```

Open the local address printed by Flask. Page 1 accepts a client ID such as
`MT_001`, shows annual metrics, and lets the user select the pie-chart basis:
Total kWh, Mean kWh/day, Max daily kWh, or Peak kW. The chart shows each year's
share of the sum of that selected metric across the client's available years.
A separate bar comparison identifies highest/lowest years by Total kWh. Page 2
accepts a year, ranking metric, and Top K (1 through 370), then highlights the
highest and lowest clients by that metric and lists the top K.

Pie slices compare a single selected metric across years. The four measures are
not combined into one pie because kW and kWh/day are different units.

The source is approximately 711 MB;
preparation streams it and writes a daily client TSV. It does not load the full
input into memory.

## Optional MongoDB

Start a local MongoDB service, then run:

```powershell
python -m electricity mongo --daily "data/prepared/electricity/daily.tsv" --database electricity_2011_2014
```

The MongoDB command imports daily client records and aggregates annual energy,
mean daily energy, maximum daily energy, and peak kW.

## Hadoop, Pig, and Hive

The distributed toolchain is set up separately; see
[docs/THREE-SYSTEM-RUN.md](docs/THREE-SYSTEM-RUN.md). Python preparation writes
`daily.tsv`; Hadoop Streaming, Pig, and Hive consume that same normalized data.
The Mapper/Reducer can also be cross-checked locally by the `analyze` command.

## Project guide

- [Architecture](docs/ARCHITECTURE.md)
- [Laptop demo](docs/LAPTOP-DEMO.md)
- [Three-system walkthrough](docs/THREE-SYSTEM-RUN.md)
- [Presentation Q&A](docs/PRESENTATION-QA.md)
- [Hadoop cluster assignment Q&A](docs/possibleQA.md)
- [Report outline](docs/report-outline.md)
- [Validation record](docs/validation.md)
- [Technical reference](docs/TECHNICAL-REFERENCE.md)

The large source file, generated `data/`, and `results/` are local and excluded
from Git. Use a new output directory for every preparation or analysis run.
