import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from electricity.analytics import analyze, year_client_ranking
from electricity.dashboard import create_app
from electricity.prepare import prepare


class ElectricityWorkflowTests(unittest.TestCase):
    def make_source(self, path, bad_value=None):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["", "MT_001", "MT_002"])
            timestamp = datetime(2020, 1, 1, 0, 15)
            for index in range(192):
                first = "1,0" if index < 96 else "2,0"
                if bad_value is not None and index == 0:
                    first = bad_value
                writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), first, "0"])
                timestamp += timedelta(minutes=15)

    def test_preparation_analysis_and_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            self.make_source(source)
            manifest = prepare(source, root / "prepared")
            self.assertEqual(manifest["clients"], 2)
            self.assertEqual(manifest["interval_rows"], 192)
            self.assertEqual(manifest["daily_client_rows"], 4)
            self.assertEqual(manifest["first_day"], "2020-01-01")
            self.assertEqual(manifest["last_day"], "2020-01-02")
            output = root / "results"
            result = analyze(root / "prepared/daily.tsv", output)
            self.assertEqual(result["mapreduce_crosscheck"], "passed")
            self.assertEqual(result["total_energy_kwh"], 72.0)
            annual = next(row for row in result["records"] if row["client_id"] == "MT_001")
            self.assertEqual(annual["days"], 2)
            self.assertEqual(annual["energy_kwh"], 72.0)
            self.assertEqual(annual["mean_daily_kwh"], 36.0)
            self.assertEqual(annual["max_daily_kwh"], 48.0)
            self.assertEqual(annual["peak_kw"], 2.0)
            peak_ranking = year_client_ranking(result, 2020, "peak_kw", 1)
            self.assertEqual(peak_ranking["most"]["client_id"], "MT_001")
            self.assertEqual(peak_ranking["least"]["client_id"], "MT_002")
            self.assertEqual(len(peak_ranking["clients"]), 1)
            with self.assertRaisesRegex(ValueError, "Top K"):
                year_client_ranking(result, 2020, "peak_kw", 3)
            response = create_app(output).test_client().get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Power, in perspective.", response.data)
            for brand_color in (b"#7F011F", b"#F5EBD0", b"#890149", b"#F3F3E7"):
                self.assertIn(brand_color, response.data)
            client_page = create_app(output).test_client().get("/?client_id=mt_001")
            self.assertEqual(client_page.status_code, 200)
            self.assertIn(b"Yearly share", client_page.data)
            self.assertIn(b"used the most energy in", client_page.data)
            self.assertIn(b"Mean kWh/day", client_page.data)
            for metric, label in (("energy_kwh", "Total kWh"),
                                  ("mean_daily_kwh", "Mean kWh/day"),
                                  ("max_daily_kwh", "Max daily kWh"),
                                  ("peak_kw", "Peak kW")):
                response = create_app(output).test_client().get(
                    f"/?client_id=MT_001&pie_metric={metric}")
                self.assertEqual(response.status_code, 200)
                self.assertIn(label.encode(), response.data)
            year_page = create_app(output).test_client().get("/?page=year&year=2020")
            self.assertEqual(year_page.status_code, 200)
            self.assertIn(b"Highest Total kWh", year_page.data)
            self.assertIn(b"Lowest Total kWh", year_page.data)
            self.assertIn(b"MT_001", year_page.data)
            self.assertIn(b"MT_002", year_page.data)
            top_one = create_app(output).test_client().get(
                "/?page=year&year=2020&metric=peak_kw&top_k=1")
            self.assertEqual(top_one.status_code, 200)
            self.assertIn(b"Rank clients by", top_one.data)
            self.assertIn(b"Peak kW", top_one.data)
            self.assertIn(b"Top 1 clients", top_one.data)
            self.assertEqual(top_one.data.count(b"<tbody>"), 1)

    def test_dashboard_handles_unknown_client_and_invalid_year(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            self.make_source(source)
            prepare(source, root / "prepared")
            analyze(root / "prepared/daily.tsv", root / "results")
            client = create_app(root / "results").test_client()
            missing = client.get("/?client_id=MT_999")
            self.assertEqual(missing.status_code, 200)
            self.assertIn(b"No data found", missing.data)
            self.assertEqual(client.get("/?page=year&year=2025").status_code, 400)
            self.assertEqual(client.get("/?page=unknown").status_code, 400)
            self.assertEqual(client.get("/?page=year&year=2020&top_k=0").status_code, 400)
            self.assertEqual(client.get("/?page=year&year=2020&top_k=not-a-number").status_code, 400)
            self.assertEqual(client.get("/?page=year&year=2020&metric=unknown").status_code, 400)
            self.assertEqual(client.get("/?client_id=MT_001&pie_metric=unknown").status_code, 400)

    def test_zero_values_are_preserved_and_bad_values_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            self.make_source(source)
            prepared = root / "prepared"
            prepare(source, prepared)
            with (prepared / "daily.tsv").open(encoding="utf-8") as stream:
                rows = list(csv.reader(stream, delimiter="\t"))
            self.assertEqual([row[3] for row in rows if row[1] == "MT_002"], ["0", "0"])

            malformed = root / "malformed.txt"
            self.make_source(malformed, bad_value="")
            with self.assertRaisesRegex(ValueError, "Missing reading"):
                prepare(malformed, root / "bad-output")

    def test_timestamp_midnight_is_assigned_to_previous_interval_day(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            self.make_source(source)
            prepared = root / "prepared"
            prepare(source, prepared)
            with (prepared / "daily.tsv").open(encoding="utf-8") as stream:
                rows = list(csv.reader(stream, delimiter="\t"))
            self.assertEqual({row[0] for row in rows}, {"2020-01-01", "2020-01-02"})

    def test_analytics_rejects_incomplete_daily_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            daily = root / "daily.tsv"
            daily.write_text("2020-01-01\tMT_001\t95\t1\t1\t1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "96 intervals"):
                analyze(daily, root / "results")
            self.assertFalse((root / "results/analytics.json").exists())


if __name__ == "__main__":
    unittest.main()
