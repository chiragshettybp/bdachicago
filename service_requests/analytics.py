"""Reference annual service request summaries and local streaming MapReduce execution."""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path


METRICS = {
    "requests": {"label": "Total requests", "unit": "requests"},
    "mean_daily_requests": {"label": "Mean requests/day", "unit": "requests/day"},
    "max_daily_requests": {"label": "Max daily requests", "unit": "requests"},
    "avg_resolution_days": {"label": "Avg resolution days", "unit": "days"},
}

REAL_EXAMPLES = [
    {"sr_type": "311 INFORMATION ONLY CALL", "short_code": "311IOC",
     "department": "311 City Services", "count": 4921249},
    {"sr_type": "Aircraft Noise Complaint", "short_code": "AVN",
     "department": "Aviation", "count": 2389257},
    {"sr_type": "Graffiti Removal Request", "short_code": "GRAF",
     "department": "Streets and Sanitation", "count": 679929},
    {"sr_type": "Pothole in Street Complaint", "short_code": "PHF",
     "department": "CDOT - Department of Transportation", "count": 405198},
    {"sr_type": "Street Light Out Complaint", "short_code": "SFD",
     "department": "CDOT - Department of Transportation", "count": 383743},
    {"sr_type": "Garbage Cart Maintenance", "short_code": "SIE",
     "department": "Streets and Sanitation", "count": 365054},
    {"sr_type": "Rodent Baiting/Rat Complaint", "short_code": "SGA",
     "department": "Streets and Sanitation", "count": 360908},
    {"sr_type": "Abandoned Vehicle Complaint", "short_code": "SKA",
     "department": "Streets and Sanitation", "count": 312633},
    {"sr_type": "Tree Debris Clean-Up Request", "short_code": "SEL",
     "department": "Streets and Sanitation", "count": 191042},
    {"sr_type": "Traffic Signal Out Complaint", "short_code": "SFB",
     "department": "CDOT - Department of Transportation", "count": 176755},
    {"sr_type": "Building Violation", "short_code": "BBA",
     "department": "DOB - Buildings", "count": 158130},
    {"sr_type": "Water Lead Test Kit Request", "short_code": "WCA2",
     "department": "DWM - Department of Water Management", "count": 110504},
    {"sr_type": "Dead Animal Pick-Up Request", "short_code": "SGQ",
     "department": "Streets and Sanitation", "count": 101460},
]


def reference(daily_path):
    groups = {}
    with Path(daily_path).open(encoding="utf-8", newline="") as stream:
        for row_number, fields in enumerate(csv.reader(stream, delimiter="\t"), start=1):
            if len(fields) != 6:
                raise ValueError(f"Expected six fields in daily row {row_number}")
            day, sr_type, requests, completed, canceled, resolution_days = fields
            if not day or not sr_type:
                raise ValueError(f"Invalid daily row {row_number}")
            try:
                request_count = int(requests)
                completed_count = int(completed)
                canceled_count = int(canceled)
                resolution_total = float(resolution_days)
            except ValueError as error:
                raise ValueError(f"Invalid numeric value in daily row {row_number}") from error
            if request_count < 0 or completed_count < 0 or canceled_count < 0:
                raise ValueError(f"Invalid negative count in daily row {row_number}")
            if not math.isfinite(resolution_total) or resolution_total < 0:
                raise ValueError(f"Invalid resolution value in daily row {row_number}")
            year = int(day[:4])
            key = (sr_type, year)
            item = groups.setdefault(key, {
                "days": 0,
                "requests": 0,
                "max_daily_requests": 0,
                "resolution_days": 0.0,
                "completed": 0,
            })
            item["days"] += 1
            item["requests"] += request_count
            item["max_daily_requests"] = max(item["max_daily_requests"], request_count)
            item["resolution_days"] += resolution_total
            item["completed"] += completed_count
    for item in groups.values():
        item["mean_daily_requests"] = item["requests"] / item["days"] if item["days"] else 0.0
        item["avg_resolution_days"] = (
            item["resolution_days"] / item["completed"] if item["completed"] else 0.0
        )
    return groups


def local_mapreduce(daily_path, output_path):
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
        sr_type, year, days, total, mean, maximum, avg_resolution = fields
        key = (sr_type, int(year))
        if key in result:
            raise ValueError(f"Duplicate MapReduce summary for {key}")
        result[key] = {
            "days": int(days),
            "requests": float(total),
            "mean_daily_requests": float(mean),
            "max_daily_requests": float(maximum),
            "avg_resolution_days": float(avg_resolution),
        }
    return result


def check(expected, actual):
    if expected.keys() != actual.keys():
        raise ValueError("MapReduce and reference summaries contain different service request type/year groups")
    for key, left in expected.items():
        right = actual[key]
        if left["days"] != right["days"]:
            raise ValueError(f"Summary mismatch for {key}: days")
        for field in ("requests", "mean_daily_requests", "max_daily_requests", "avg_resolution_days"):
            if not math.isclose(left[field], right[field], rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError(f"Summary mismatch for {key}: {field}")


def analyze(daily_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    groups = reference(daily_path)
    mr_text = local_mapreduce(daily_path, output_dir / "mapreduce.tsv")
    check(groups, read_mapreduce(mr_text))
    records = [{"sr_type": sr_type, "year": year, **value}
               for (sr_type, year), value in sorted(groups.items())]
    # Normalize field names for dashboard: requests stays requests; ensure metric keys exist.
    for row in records:
        row.setdefault("requests", row.get("requests", 0))
    result = {
        "dataset": "Chicago 311 Service Requests",
        "summary": "Annual service request summaries by request type",
        "groups": len(records),
        "total_requests": sum(row["requests"] for row in records),
        "service_request_types": len({row["sr_type"] for row in records}),
        "clients": len({row["sr_type"] for row in records}),
        "years": sorted({row["year"] for row in records}),
        "mapreduce_crosscheck": "passed",
        "records": records,
    }
    # Dashboard expects client_id-like? Provide sr_type as client_id alias for compatibility.
    for row in records:
        row["client_id"] = row["sr_type"]
    (output_dir / "analytics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def client_year_view(data, client_id, pie_metric="requests"):
    """Return one service request type's available yearly records in chronological order."""
    if pie_metric not in METRICS:
        raise ValueError("Unsupported client pie-chart metric")
    needle = (client_id or "").casefold()
    records = sorted(
        (row for row in data["records"] if row["sr_type"].casefold() == needle or str(row.get("client_id", "")).casefold() == needle),
        key=lambda row: row["year"],
    )
    if not records:
        return None
    highest = max(records, key=lambda row: (row["requests"], -row["year"]))
    lowest = min(records, key=lambda row: (row["requests"], row["year"]))
    return {
        "client_id": client_id,
        "records": records,
        "highest_year": highest["year"],
        "lowest_year": lowest["year"],
        "pie_metric": pie_metric,
        "pie_total": sum(row[pie_metric] for row in records),
    }


def year_client_ranking(data, year, metric="requests", top_k=10):
    """Rank service request types by a selected annual metric and return the requested top K."""
    if metric not in METRICS:
        raise ValueError("Unsupported client ranking metric")
    max_k = data.get("clients", data.get("service_request_types", 1))
    if type(top_k) is not int or not 1 <= top_k <= max_k:
        raise ValueError(f"Top K must be between 1 and {max_k}")
    records = sorted(
        (row for row in data["records"] if row["year"] == year),
        key=lambda row: (-row[metric], row["sr_type"]),
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
