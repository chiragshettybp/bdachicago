"""Optional MongoDB persistence and aggregation for prepared daily readings."""

import csv
import math
import os
import re
from pathlib import Path

from pymongo import MongoClient


def import_and_analyze(daily_path, database, batch_size=2000):
    if not re.fullmatch(r"electricity_[A-Za-z0-9_]+", database):
        raise ValueError("Use a dedicated database named electricity_<name>")
    if not 1 <= batch_size <= 10000:
        raise ValueError("batch-size must be between 1 and 10000")
    client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017"),
                         serverSelectionTimeoutMS=10000)
    try:
        client.admin.command("ping")
        db = client[database]
        if db.list_collection_names():
            raise ValueError("Destination database is not empty; choose a new database")
        daily = db.daily_readings
        batch = []
        count = 0
        with Path(daily_path).open(encoding="utf-8", newline="") as stream:
            for fields in csv.reader(stream, delimiter="\t"):
                if len(fields) != 6:
                    raise ValueError(f"Malformed daily row {count + 1}")
                day, customer, intervals, energy, mean_kw, peak_kw = fields
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or not re.fullmatch(r"MT_\d{3}", customer):
                    raise ValueError(f"Invalid date or client ID in daily row {count + len(batch) + 1}")
                try:
                    values = tuple(map(float, (energy, mean_kw, peak_kw)))
                except ValueError as error:
                    raise ValueError(f"Invalid numeric value in daily row {count + len(batch) + 1}") from error
                if (int(intervals) != 96 or
                        any(not math.isfinite(value) or value < 0 for value in values)):
                    raise ValueError(f"Invalid daily summary in row {count + len(batch) + 1}")
                batch.append({"date": day, "client_id": customer, "year": int(day[:4]),
                              "intervals": int(intervals), "energy_kwh": values[0],
                              "mean_kw": values[1], "peak_kw": values[2]})
                if len(batch) >= batch_size:
                    daily.insert_many(batch, ordered=True)
                    count += len(batch)
                    batch.clear()
            if batch:
                daily.insert_many(batch, ordered=True)
                count += len(batch)
        daily.create_index([("client_id", 1), ("year", 1)], name="client_year")
        daily.create_index([("date", 1)], name="date")
        pipeline = [
            {"$group": {"_id": {"client_id": "$client_id", "year": "$year"},
                        "days": {"$sum": 1}, "energy_kwh": {"$sum": "$energy_kwh"},
                        "max_daily_kwh": {"$max": "$energy_kwh"}, "peak_kw": {"$max": "$peak_kw"}}},
            {"$project": {"_id": 0, "client_id": "$_id.client_id", "year": "$_id.year",
                          "days": 1, "energy_kwh": 1, "max_daily_kwh": 1, "peak_kw": 1,
                          "mean_daily_kwh": {"$divide": ["$energy_kwh", "$days"]}}},
            {"$sort": {"client_id": 1, "year": 1}},
        ]
        summaries = list(daily.aggregate(pipeline, allowDiskUse=True))
        return {"database": database, "daily_rows": count, "summaries": summaries}
    finally:
        client.close()
