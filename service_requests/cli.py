"""Command-line workflows for the Chicago 311 Service Requests dataset."""

import argparse
import json
from pathlib import Path

from .analytics import analyze
from .prepare import prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare", help="Validate and create daily service request rows")
    preparation.add_argument("--input", required=True, help="Path to 311 Service Requests CSV export")
    preparation.add_argument("--output", required=True, help="New output directory")
    analysis = commands.add_parser("analyze", help="Cross-check annual service request summaries locally")
    analysis.add_argument("--daily", required=True, help="Prepared daily.tsv")
    analysis.add_argument("--output", required=True, help="New output directory")
    mongo = commands.add_parser("mongo", help="Import daily rows and aggregate them in MongoDB")
    mongo.add_argument("--daily", required=True, help="Prepared daily.tsv")
    mongo.add_argument("--database", default="service_requests_311")
    mongo.add_argument("--batch-size", type=int, default=2000)
    dashboard = commands.add_parser("dashboard", help="Serve saved analytics in the local Flask dashboard")
    dashboard.add_argument("--results", default="results/service_requests")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    if args.command == "prepare":
        result = prepare(args.input, args.output)
    elif args.command == "analyze":
        result = analyze(args.daily, args.output)
    elif args.command == "mongo":
        from .mongo import import_and_analyze
        result = import_and_analyze(args.daily, args.database, args.batch_size)
    else:
        from .dashboard import create_app
        create_app(Path(args.results)).run(host=args.host, port=args.port, debug=False)
        return
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
