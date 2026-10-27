"""Convert the Chicago 311 Service Requests CSV export to daily request summaries."""

import csv
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path


REQUIRED_COLUMNS = ("SR_NUMBER", "SR_TYPE", "CREATED_DATE")
STATUS_COMPLETED = {"COMPLETED", "CLOSED"}
STATUS_CANCELED = {"CANCELED", "CANCELLED"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_timestamp(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    formats = (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid timestamp: {raw!r}")


def _detect_delimiter(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        first_line = stream.readline()
    if ";" in first_line and first_line.count(";") > first_line.count(","):
        return ";"
    return ","


def prepare(source, destination):
    """Stream 311 service requests into one row per service request type and day."""
    source = Path(source).resolve(strict=True)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    daily_path = destination / "daily.tsv"
    delimiter = _detect_delimiter(source)

    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("The source CSV has no header row")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        aggregates = {}
        total_rows = 0
        first_created = None
        last_created = None
        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            sr_number = (row.get("SR_NUMBER") or "").strip()
            sr_type = (row.get("SR_TYPE") or "").strip()
            if not sr_number:
                raise ValueError(f"Missing SR_NUMBER at source row {row_number}")
            if not sr_type:
                raise ValueError(f"Missing SR_TYPE at source row {row_number}")
            created = _parse_timestamp(row.get("CREATED_DATE"))
            if created is None:
                raise ValueError(f"Missing CREATED_DATE at source row {row_number}")
            if first_created is None or created < first_created:
                first_created = created
            if last_created is None or created > last_created:
                last_created = created

            day = created.date()
            status = (row.get("STATUS") or "").strip().upper()
            completed = 1 if status in STATUS_COMPLETED else 0
            canceled = 1 if status in STATUS_CANCELED else 0

            closed_raw = row.get("CLOSED_DATE")
            resolution_days = 0.0
            if completed and closed_raw:
                closed = _parse_timestamp(closed_raw)
                if closed is not None and closed >= created:
                    resolution_days = (closed - created).total_seconds() / 86400.0

            key = (day, sr_type)
            item = aggregates.setdefault(key, {
                "requests": 0, "completed": 0, "canceled": 0, "resolution_days": 0.0,
            })
            item["requests"] += 1
            item["completed"] += completed
            item["canceled"] += canceled
            item["resolution_days"] += resolution_days

    if not aggregates:
        raise ValueError("The source contains no service requests")

    daily_count = 0
    with daily_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        for (day, sr_type) in sorted(aggregates):
            item = aggregates[(day, sr_type)]
            writer.writerow((
                day.isoformat(),
                sr_type,
                item["requests"],
                item["completed"],
                item["canceled"],
                format(item["resolution_days"], ".15g"),
            ))
            daily_count += 1

    record = {
        "dataset": "Chicago 311 Service Requests",
        "source_file": source.name,
        "source_sha256": sha256(source),
        "service_request_types": len({key[1] for key in aggregates}),
        "clients": len({key[1] for key in aggregates}),
        "source_rows": total_rows,
        "interval_rows": total_rows,
        "daily_type_rows": daily_count,
        "daily_client_rows": daily_count,
        "days": len({key[0] for key in aggregates}),
        "first_created_date": first_created.isoformat(sep=" ") if first_created else None,
        "last_created_date": last_created.isoformat(sep=" ") if last_created else None,
        "first_day": min(key[0] for key in aggregates).isoformat(),
        "last_day": max(key[0] for key in aggregates).isoformat(),
        "daily_columns": ["date", "sr_type", "requests", "completed", "canceled", "resolution_days"],
        "conversion": "One daily row per service request type and creation date",
    }
    (destination / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record
