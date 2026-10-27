import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from service_requests.analytics import analyze, year_client_ranking
from service_requests.dashboard import create_app
from service_requests.prepare import prepare


class ServiceRequestWorkflowTests(unittest.TestCase):
    def make_source(self, path, bad_value=None):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["SR_NUMBER", "SR_TYPE", "STATUS", "CREATED_DATE", "CLOSED_DATE"])
            timestamp = datetime(2020, 1, 1, 8, 0)
            for index in range(10):
                sr_type = "Pothole in Street Complaint" if index < 6 else "Graffiti Removal Request"
                status = "Completed" if index % 2 == 0 else "Open"
                created = timestamp + timedelta(days=index // 3)
                closed = created + timedelta(days=2) if status == "Completed" else ""
                if bad_value is not None and index == 0:
                    created = bad_value
                created_value = created if isinstance(created, str) else created.isoformat()
                closed_value = closed if isinstance(closed, str) else (closed.isoformat() if closed else "")
                writer.writerow([f"SR{index}", sr_type, status, created_value, closed_value])

    def test_preparation_analysis_and_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            self.make_source(source)
            manifest = prepare(source, root / "prepared")
            self.assertEqual(manifest["service_request_types"], 2)
            self.assertEqual(manifest["source_rows"], 10)
            output = root / "results"
            result = analyze(root / "prepared/daily.tsv", output)
            self.assertEqual(result["mapreduce_crosscheck"], "passed")
            self.assertEqual(result["total_requests"], 10)
            self.assertEqual(result["clients"], 2)
            ranking = year_client_ranking(result, 2020, "requests", 1)
            self.assertEqual(len(ranking["clients"]), 1)
            response = create_app(output).test_client().get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"City services, in perspective.", response.data)
            client_page = create_app(output).test_client().get(
                "/?client_id=Pothole+in+Street+Complaint")
            self.assertEqual(client_page.status_code, 200)
            self.assertIn(b"had the most requests in", client_page.data)
            examples_page = create_app(output).test_client().get("/?page=examples")
            self.assertEqual(examples_page.status_code, 200)
            self.assertIn(b"Real examples", examples_page.data)
            self.assertIn(b"Pothole in Street Complaint", examples_page.data)
            self.assertIn(b"in loaded results", examples_page.data)
            self.assertIn(b"Year ranking links", examples_page.data)

    def test_dashboard_handles_unknown_and_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            self.make_source(source)
            prepare(source, root / "prepared")
            analyze(root / "prepared/daily.tsv", root / "results")
            client = create_app(root / "results").test_client()
            missing = client.get("/?client_id=Unknown+Type")
            self.assertEqual(missing.status_code, 200)
            self.assertIn(b"No data found", missing.data)
            self.assertEqual(client.get("/?page=year&year=2025").status_code, 400)
            self.assertEqual(client.get("/?page=unknown").status_code, 400)

    def test_examples_page_works_without_analytics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = create_app(root / "missing-results")
            page = app.test_client().get("/?page=examples")
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"Real examples", page.data)
            self.assertIn(b"No analytics loaded", page.data)

    def test_bad_values_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            self.make_source(source, bad_value="")
            with self.assertRaisesRegex(ValueError, "Missing CREATED_DATE|Invalid timestamp"):
                prepare(source, root / "bad-output")


if __name__ == "__main__":
    unittest.main()
