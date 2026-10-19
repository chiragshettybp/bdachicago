"""Convert the UCI wide-format electricity file to daily client summaries."""

import csv
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path


INTERVAL = timedelta(minutes=15)
CLIENT_PATTERN = re.compile(r"MT_[0-9]{3}\Z")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(raw, row_number, client):
    if not raw:
        raise ValueError(f"Missing reading for {client} at source row {row_number}")
    try:
        value = float(raw.replace(",", "."))
    except ValueError as error:
        raise ValueError(f"Invalid reading for {client} at source row {row_number}: {raw!r}") from error
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid non-finite or negative reading for {client} at source row {row_number}")
    return value


def prepare(source, destination):
    """Stream source readings into one row per client and interval-end day."""
    source = Path(source).resolve(strict=True)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    daily_path = destination / "daily.tsv"
    interval_count = 0
    daily_count = 0
    first_timestamp = None
    last_timestamp = None
    current_day = None
    sums = peaks = None
    clients = None

    def write_day(writer, day, totals, maxima, count):
        nonlocal daily_count
        if count != 96:
            raise ValueError(f"Expected 96 intervals for {day}, found {count}")
        for index, client in enumerate(clients):
            energy = totals[index]
            writer.writerow((day.isoformat(), client, count, format(energy, ".15g"),
                             format(energy * 4 / count, ".15g"), format(maxima[index], ".15g")))
            daily_count += 1

    with source.open(encoding="utf-8-sig", newline="") as stream, \
            daily_path.open("w", encoding="utf-8", newline="") as output:
        reader = csv.reader(stream, delimiter=";", quotechar='"')
        header = next(reader, None)
        if not header or header[0] != "" or len(header) < 2:
            raise ValueError("Expected an empty first header followed by client IDs")
        clients = header[1:]
        if len(set(clients)) != len(clients) or any(not CLIENT_PATTERN.fullmatch(c) for c in clients):
            raise ValueError("Client IDs must be unique MT_NNN values")
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")

        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(clients) + 1:
                raise ValueError(f"Expected {len(clients) + 1} fields at source row {row_number}, got {len(row)}")
            try:
                timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            except ValueError as error:
                raise ValueError(f"Invalid timestamp at source row {row_number}: {row[0]!r}") from error
            if last_timestamp is not None and timestamp - last_timestamp != INTERVAL:
                raise ValueError(f"Expected consecutive 15-minute timestamps at source row {row_number}")
            if first_timestamp is None:
                first_timestamp = timestamp
            last_timestamp = timestamp
            day = (timestamp - INTERVAL).date()
            if current_day is None:
                current_day = day
                sums = [0.0] * len(clients)
                peaks = [0.0] * len(clients)
                day_intervals = 0
            elif day != current_day:
                write_day(writer, current_day, sums, peaks, day_intervals)
                if day != current_day + timedelta(days=1):
                    raise ValueError(f"Missing daily data between {current_day} and {day}")
                current_day = day
                sums = [0.0] * len(clients)
                peaks = [0.0] * len(clients)
                day_intervals = 0
            for index, (client, raw) in enumerate(zip(clients, row[1:])):
                kw = _number(raw, row_number, client)
                sums[index] += kw / 4
                peaks[index] = max(peaks[index], kw)
            day_intervals += 1
            interval_count += 1
        if current_day is None:
            raise ValueError("The source contains no readings")
        write_day(writer, current_day, sums, peaks, day_intervals)

    record = {
        "dataset": "UCI ElectricityLoadDiagrams20112014",
        "source_file": source.name,
        "source_sha256": sha256(source),
        "clients": len(clients),
        "interval_minutes": 15,
        "interval_rows": interval_count,
        "daily_client_rows": daily_count,
        "days": daily_count // len(clients),
        "first_interval_end": first_timestamp.isoformat(sep=" "),
        "last_interval_end": last_timestamp.isoformat(sep=" "),
        "first_day": (first_timestamp - INTERVAL).date().isoformat(),
        "last_day": (last_timestamp - INTERVAL).date().isoformat(),
        "daily_columns": ["date", "client_id", "intervals", "energy_kwh", "mean_kw", "peak_kw"],
        "conversion": "energy_kwh is the sum of each 15-minute kW reading divided by 4",
        "timestamp_note": "Each timestamp labels the interval end; midnight belongs to the preceding day.",
        "zero_note": "Zero readings are retained, including zero-filled periods before a client appears.",
        "dst_note": "The source's 96-reading Portugal-time DST conventions are preserved; interpret time-of-day comparisons with care.",
    }
    (destination / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record
