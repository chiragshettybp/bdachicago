"""Read-only Flask dashboard for saved electricity analytics."""

import json
from pathlib import Path

from flask import Flask, abort, render_template, request

from .analytics import METRICS, client_year_view, year_client_ranking


def create_app(results_dir):
    app = Flask(__name__)
    results_dir = Path(results_dir).resolve()

    @app.get("/")
    def home():
        path = results_dir / "analytics.json"
        if not path.is_file():
            abort(404, description=f"No analytics found at {path}")
        with path.open(encoding="utf-8") as source:
            data = json.load(source)
        page = request.args.get("page", "client")
        if page not in {"client", "year"}:
            abort(400, description="Choose the client or year view")
        years = sorted(data["years"])
        default_top_k = min(10, data["clients"])
        if page == "client":
            client_id = request.args.get("client_id", "").strip().upper()
            if len(client_id) > 20:
                abort(400, description="Client ID is too long")
            pie_metric = request.args.get("pie_metric", "energy_kwh")
            if pie_metric not in METRICS:
                abort(400, description="Choose a supported pie-chart metric")
            client = client_year_view(data, client_id, pie_metric) if client_id else None
            return render_template("dashboard.html", data=data, page=page, years=years,
                                   selected_year=years[0] if years else None,
                                   client=client, client_id=client_id, ranking=None,
                                   metrics=METRICS, pie_metric=pie_metric,
                                   rank_metric="energy_kwh", top_k=default_top_k)

        raw_year = request.args.get("year", str(years[0] if years else ""))
        try:
            selected_year = int(raw_year)
        except ValueError:
            abort(400, description="Select a valid year")
        if selected_year not in years:
            abort(400, description="The selected year is not in this dataset")
        rank_metric = request.args.get("metric", "energy_kwh")
        if rank_metric not in METRICS:
            abort(400, description="Choose a supported ranking metric")
        raw_top_k = request.args.get("top_k", str(default_top_k))
        try:
            top_k = int(raw_top_k)
        except ValueError:
            abort(400, description="Top K must be a whole number")
        if not 1 <= top_k <= data["clients"]:
            abort(400, description=f"Top K must be between 1 and {data['clients']}")
        ranking = year_client_ranking(data, selected_year, rank_metric, top_k)
        return render_template("dashboard.html", data=data, page=page, years=years,
                               selected_year=selected_year, client=None, client_id="",
                               ranking=ranking, metrics=METRICS, pie_metric="energy_kwh",
                               rank_metric=rank_metric, top_k=top_k)

    return app
