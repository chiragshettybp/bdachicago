"""Profile MongoDB queries against an imported electricity dataset."""

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


def profile_database(database, client_id, output_path):
    if not re.fullmatch(r"electricity_[A-Za-z0-9_]+", database):
        raise ValueError("Use the imported database named electricity_<name>")
    if not re.fullmatch(r"MT_\d{3}", client_id):
        raise ValueError("client-id must look like MT_001")

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

        query = {"client_id": client_id, "year": {"$gte": 2011, "$lte": 2014}}
        find_explain = client[database].command(
            "explain",
            {
                "find": "daily_readings",
                "filter": query,
                "projection": {"_id": 0, "date": 1, "energy_kwh": 1},
                "limit": 100,
            },
            verbosity="executionStats",
        )
        aggregation = [
            {"$match": {"client_id": client_id}},
            {
                "$group": {
                    "_id": "$year",
                    "days": {"$sum": 1},
                    "energy_kwh": {"$sum": "$energy_kwh"},
                    "max_daily_kwh": {"$max": "$energy_kwh"},
                    "peak_kw": {"$max": "$peak_kw"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id",
                    "days": 1,
                    "energy_kwh": 1,
                    "mean_daily_kwh": {"$divide": ["$energy_kwh", "$days"]},
                    "max_daily_kwh": 1,
                    "peak_kw": 1,
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
            "client_id": client_id,
            "document_count": document_count,
            "indexes": {
                name: {"keys": details["key"], "unique": details.get("unique", False)}
                for name, details in indexes.items()
            },
            "query_profile": {
                "description": "Find daily records for one client across 2011-2014",
                "explain_execution_stats": _execution_summaries(find_explain),
            },
            "aggregation_profile": {
                "description": "Group the selected client's daily records by year",
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
    parser.add_argument("--database", default="electricity_2011_2014")
    parser.add_argument("--client-id", default="MT_001")
    parser.add_argument("--output", default="results/mongodb-analytics.json")
    args = parser.parse_args()
    report = profile_database(args.database, args.client_id, args.output)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
