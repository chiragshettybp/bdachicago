"""Optional MongoDB persistence and aggregation for prepared daily readings."""

import csv
import math
import os
import re
from pathlib import Path

from pymongo import MongoClient


def import_and_analyze(daily_path, database, batch_size=2000):
    if not re.fullmatch(r"(service_requests|chicago311)_[A-Za-z0-9_]+", database):
        raise ValueError("Use a dedicated database named service_requests_<name>")
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
                day, sr_type, requests, completed, canceled, resolution_days = fields
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or not sr_type.strip():
                    raise ValueError(f"Invalid date or service request type in daily row {count + len(batch) + 1}")
                try:
                    request_count = int(requests)
                    completed_count = int(completed)
                    canceled_count = int(canceled)
                    resolution_total = float(resolution_days)
                except ValueError as error:
                    raise ValueError(f"Invalid numeric value in daily row {count + len(batch) + 1}") from error
                if request_count < 0 or completed_count < 0 or canceled_count < 0:
                    raise ValueError(f"Invalid daily summary in row {count + len(batch) + 1}")
                if not math.isfinite(resolution_total) or resolution_total < 0:
                    raise ValueError(f"Invalid daily summary in row {count + len(batch) + 1}")
                batch.append({"date": day, "sr_type": sr_type, "year": int(day[:4]),
                              "requests": request_count, "completed": completed_count,
                              "canceled": canceled_count, "resolution_days": resolution_total})
                if len(batch) >= batch_size:
                    daily.insert_many(batch, ordered=True)
                    count += len(batch)
                    batch.clear()
            if batch:
                daily.insert_many(batch, ordered=True)
                count += len(batch)
        daily.create_index([("sr_type", 1), ("year", 1)], name="type_year")
        daily.create_index([("date", 1)], name="date")
        pipeline = [
            {"$group": {"_id": {"sr_type": "$sr_type", "year": "$year"},
                        "days": {"$sum": 1}, "requests": {"$sum": "$requests"},
                        "max_daily_requests": {"$max": "$requests"},
                        "resolution_days": {"$sum": "$resolution_days"},
                        "completed": {"$sum": "$completed"}}},
            {"$project": {"_id": 0, "sr_type": "$_id.sr_type", "year": "$_id.year",
                          "days": 1, "requests": 1, "max_daily_requests": 1,
                          "mean_daily_requests": {"$divide": ["$requests", "$days"]},
                          "avg_resolution_days": {"$cond": [{"$gt": ["$completed", 0]},
                                                            {"$divide": ["$resolution_days", "$completed"]}, 0.0]}}},
            {"$sort": {"sr_type": 1, "year": 1}},
        ]
        summaries = list(daily.aggregate(pipeline, allowDiskUse=True))
        return {"database": database, "daily_rows": count, "summaries": summaries}
    finally:
        client.close()
