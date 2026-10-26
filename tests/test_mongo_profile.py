import unittest

from electricity.mongo_profile import _execution_summaries, profile_database


class MongoProfileTests(unittest.TestCase):
    def test_execution_summaries_include_nested_aggregation_stats(self):
        explain = {
            "queryPlanner": {"winningPlan": {"stage": "IXSCAN"}},
            "stages": [
                {"$cursor": {"executionStats": {
                    "nReturned": 96,
                    "executionTimeMillis": 3,
                    "totalKeysExamined": 96,
                    "totalDocsExamined": 96,
                    "executionStages": {"stage": "IXSCAN"},
                }}},
            ],
        }
        self.assertEqual(_execution_summaries(explain), [{
            "nReturned": 96,
            "executionTimeMillis": 3,
            "totalKeysExamined": 96,
            "totalDocsExamined": 96,
        }])

    def test_profile_validates_arguments_before_connecting(self):
        with self.assertRaisesRegex(ValueError, "electricity_"):
            profile_database("other_database", "MT_001", "report.json")
        with self.assertRaisesRegex(ValueError, "MT_001"):
            profile_database("electricity_demo", "bad-client", "report.json")


if __name__ == "__main__":
    unittest.main()
