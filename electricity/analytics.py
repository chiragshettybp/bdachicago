"""Reference annual client summaries and local streaming MapReduce execution."""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path


METRICS = {
    "energy_kwh": {"label": "Total kWh", "unit": "kWh"},
    "mean_daily_kwh": {"label": "Mean kWh/day", "unit": "kWh/day"},
    "max_daily_kwh": {"label": "Max daily kWh", "unit": "kWh"},
    "peak_kw": {"label": "Peak kW", "unit": "kW"},
}


def reference(daily_path):
    groups = {}
    with Path(daily_path).open(encoding="utf-8", newline="") as stream:
        for row_number, fields in enumerate(csv.reader(stream, delimiter="\t"), start=1):
            if len(fields) != 6:
                raise ValueError(f"Expected six fields in daily row {row_number}")
            day, client, intervals, energy, mean_kw, peak_kw = fields
            if int(intervals) != 96:
                raise ValueError(f"Expected 96 intervals in daily row {row_number}")
            values = tuple(map(float, (energy, mean_kw, peak_kw)))
            if any(not math.isfinite(value) or value < 0 for value in values):
                raise ValueError(f"Invalid numeric value in daily row {row_number}")
            year = int(day[:4])
            key = (client, year)
            item = groups.setdefault(key, {"days": 0, "energy_kwh": 0.0, "max_daily_kwh": 0.0, "peak_kw": 0.0})
            item["days"] += 1
            item["energy_kwh"] += values[0]
            item["max_daily_kwh"] = max(item["max_daily_kwh"], values[0])
            item["peak_kw"] = max(item["peak_kw"], values[2])
    for item in groups.values():
        item["mean_daily_kwh"] = item["energy_kwh"] / item["days"]
    return groups


def local_mapreduce(daily_path, output_path):
    """Run the same mapper and reducer entry points used by Hadoop Streaming."""
    root = Path(__file__).resolve().parent.parent
    with Path(daily_path).open("rb") as source:
        mapped = subprocess.run([sys.executable, str(root / "mapreduce/mapper.py")],
                                stdin=source, stdout=subprocess.PIPE, check=True)
    shuffled = b"".join(sorted(mapped.stdout.splitlines(keepends=True)))
    reduced = subprocess.run([sys.executable, str(root / "mapreduce/reducer.py")],
                             input=shuffled, stdout=subprocess.PIPE, check=True)
    Path(output_path).write_bytes(reduced.stdout)
    return reduced.stdout.decode("utf-8")


def read_mapreduce(text):
    result = {}
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) != 7:
            raise ValueError("MapReduce output must contain seven tab-separated fields")
        client, year, days, total, mean, maximum, peak = fields
        key = (client, int(year))
        if key in result:
            raise ValueError(f"Duplicate MapReduce summary for {key}")
        result[key] = {"days": int(days), "energy_kwh": float(total),
                       "mean_daily_kwh": float(mean), "max_daily_kwh": float(maximum),
                       "peak_kw": float(peak)}
    return result


def check(expected, actual):
    if expected.keys() != actual.keys():
        raise ValueError("MapReduce and reference summaries contain different client/year groups")
    for key, left in expected.items():
        right = actual[key]
        for field in ("days",):
            if left[field] != right[field]:
                raise ValueError(f"Summary mismatch for {key}: {field}")
        for field in ("energy_kwh", "mean_daily_kwh", "max_daily_kwh", "peak_kw"):
            if not math.isclose(left[field], right[field], rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError(f"Summary mismatch for {key}: {field}")


def analyze(daily_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    groups = reference(daily_path)
    mr_text = local_mapreduce(daily_path, output_dir / "mapreduce.tsv")
    check(groups, read_mapreduce(mr_text))
    records = [{"client_id": client, "year": year, **value}
               for (client, year), value in sorted(groups.items())]
    result = {"dataset": "UCI ElectricityLoadDiagrams20112014",
              "summary": "Annual energy and peak summaries by client",
              "groups": len(records),
              "total_energy_kwh": sum(row["energy_kwh"] for row in records),
              "clients": len({row["client_id"] for row in records}),
              "years": sorted({row["year"] for row in records}),
              "mapreduce_crosscheck": "passed",
              "records": records}
    (output_dir / "analytics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def client_year_view(data, client_id, pie_metric="energy_kwh"):
    """Return one client's available yearly records in chronological order."""
    if pie_metric not in METRICS:
        raise ValueError("Unsupported client pie-chart metric")
    records = sorted(
        (row for row in data["records"] if row["client_id"] == client_id),
        key=lambda row: row["year"],
    )
    if not records:
        return None
    highest = max(records, key=lambda row: (row["energy_kwh"], -row["year"]))
    lowest = min(records, key=lambda row: (row["energy_kwh"], row["year"]))
    return {
        "client_id": client_id,
        "records": records,
        "highest_year": highest["year"],
        "lowest_year": lowest["year"],
        "pie_metric": pie_metric,
        "pie_total": sum(row[pie_metric] for row in records),
    }


def year_client_ranking(data, year, metric="energy_kwh", top_k=10):
    """Rank clients by a selected annual metric and return the requested top K."""
    if metric not in METRICS:
        raise ValueError("Unsupported client ranking metric")
    if type(top_k) is not int or not 1 <= top_k <= data["clients"]:
        raise ValueError(f"Top K must be between 1 and {data['clients']}")
    records = sorted(
        (row for row in data["records"] if row["year"] == year),
        key=lambda row: (-row[metric], row["client_id"]),
    )
    return {
        "year": year,
        "metric": metric,
        "top_k": top_k,
        "clients": records[:top_k],
        "client_count": len(records),
        "most": records[0] if records else None,
        "least": records[-1] if records else None,
    }
