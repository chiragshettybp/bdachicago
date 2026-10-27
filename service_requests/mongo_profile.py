"""Profile MongoDB queries against an imported 311 service request dataset."""

import argparse
import json
import os
import re
from pathlib import Path

from pymongo import MongoClient


def _execution_summaries(explain):
    summaries = []

    def visit(value):
        if isinstance(value, dict):
            stats = value.get("executionStats")
            if isinstance(stats, dict):
                summaries.append({
                    key: stats[key]
                    for key in (
                        "executionSuccess",
                        "nReturned",
                        "executionTimeMillis",
                        "totalKeysExamined",
                        "totalDocsExamined",
                    )
                    if key in stats
                })
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(explain)
    return summaries


def profile_database(database, sr_type, output_path):
    if not re.fullmatch(r"(service_requests|chicago311)_[A-Za-z0-9_]+", database):
        raise ValueError("Use the imported database named service_requests_<name>")
    if not sr_type.strip():
        raise ValueError("sr-type must be a valid service request type")

    client = MongoClient(
        os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        serverSelectionTimeoutMS=10000,
    )
    try:
        client.admin.command("ping")
        daily = client[database].daily_readings
        document_count = daily.estimated_document_count()
        if document_count == 0:
            raise ValueError(
                f"No imported daily_readings documents found in database {database}"
            )

        query = {"sr_type": sr_type, "year": {"$gte": 2018, "$lte": 2026}}
        find_explain = client[database].command(
            "explain",
            {
                "find": "daily_readings",
                "filter": query,
                "projection": {"_id": 0, "date": 1, "requests": 1},
                "limit": 100,
            },
            verbosity="executionStats",
        )
        aggregation = [
            {"$match": {"sr_type": sr_type}},
            {
                "$group": {
                    "_id": "$year",
                    "days": {"$sum": 1},
                    "requests": {"$sum": "$requests"},
                    "max_daily_requests": {"$max": "$requests"},
                    "resolution_days": {"$sum": "$resolution_days"},
                    "completed": {"$sum": "$completed"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id",
                    "days": 1,
                    "requests": 1,
                    "mean_daily_requests": {"$divide": ["$requests", "$days"]},
                    "max_daily_requests": 1,
                    "avg_resolution_days": {"$cond": [{"$gt": ["$completed", 0]},
                                                      {"$divide": ["$resolution_days", "$completed"]}, 0.0]},
                }
            },
            {"$sort": {"year": 1}},
        ]
        aggregate_explain = client[database].command(
            "explain",
            {
                "aggregate": "daily_readings",
                "pipeline": aggregation,
                "cursor": {},
            },
            verbosity="executionStats",
        )
        indexes = daily.index_information()
        annual_results = list(daily.aggregate(aggregation, allowDiskUse=True))

        report = {
            "database": database,
            "collection": "daily_readings",
            "sr_type": sr_type,
            "document_count": document_count,
            "indexes": {
                name: {"keys": details["key"], "unique": details.get("unique", False)}
                for name, details in indexes.items()
            },
            "query_profile": {
                "description": "Find daily records for one service request type across years",
                "explain_execution_stats": _execution_summaries(find_explain),
            },
            "aggregation_profile": {
                "description": "Group the selected service request type's daily records by year",
                "explain_execution_stats": _execution_summaries(aggregate_explain),
                "annual_results": annual_results,
            },
        }
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        return report
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="service_requests_311")
    parser.add_argument("--sr-type", default="Pothole in Street Complaint")
    parser.add_argument("--output", default="results/mongodb-analytics.json")
    args = parser.parse_args()
    report = profile_database(args.database, args.sr_type, args.output)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
