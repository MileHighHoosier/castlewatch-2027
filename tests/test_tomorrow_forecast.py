import unittest
from unittest.mock import call, patch

import tomorrow_forecast


def block(key, average_wait, samples, distinct_days):
    metadata = tomorrow_forecast._block_metadata(key)
    return {
        "key": key,
        "label": metadata["label"],
        "window": metadata["window"],
        "average_wait": average_wait,
        "samples": samples,
        "distinct_days": distinct_days,
    }


class FakeConnection:
    def __init__(self):
        self.statements = []
        self.commits = 0

    def execute(self, statement, parameters=None):
        self.statements.append(" ".join(str(statement).split()).lower())
        return []

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    def connect(self):
        return self.connection


class TomorrowForecastContractTests(unittest.TestCase):
    def test_same_weekday_evidence_controls_direction_windows_and_confidence(self):
        weekday_blocks = [
            block("morning", 20, 150, 6),
            block("midday", 40, 100, 6),
        ]
        overall_blocks = [
            block("morning", 30, 150, 8),
            block("midday", 50, 100, 8),
        ]
        engine = FakeEngine()

        with patch.object(
            tomorrow_forecast,
            "_load_block_rows",
            side_effect=[weekday_blocks, overall_blocks],
        ) as load_rows:
            result = tomorrow_forecast.get_date_forecast(
                engine,
                "Magic Kingdom",
                "2027-10-10",
            )

        self.assertEqual("2027-10-10", result["date"])
        self.assertEqual("Sunday", result["weekday"])
        self.assertEqual("America/New_York", result["timezone"])
        self.assertEqual("ready", result["status"])
        self.assertEqual("same_weekday", result["source"])
        self.assertEqual("noticeably_quieter", result["comparison"])
        self.assertEqual(-26, result["comparison_percent"])
        self.assertEqual("high", result["confidence"]["level"])
        self.assertEqual(250, result["sample_count"])
        self.assertEqual(6, result["distinct_days"])
        self.assertEqual("morning", result["best_window"]["key"])
        self.assertEqual("midday", result["peak_window"]["key"])
        self.assertIn("Prior Sundays", result["summary"])
        self.assertEqual(
            [
                call(engine.connection, "Magic Kingdom", 0),
                call(engine.connection, "Magic Kingdom"),
            ],
            load_rows.call_args_list,
        )
        self.assertEqual(1, engine.connection.commits)
        self.assertTrue(any("statement_timeout" in sql for sql in engine.connection.statements))

    def test_sparse_weekday_history_falls_back_to_overall_baseline(self):
        weekday_blocks = [block("morning", 10, 39, 1)]
        overall_blocks = [
            block("morning", 25, 20, 4),
            block("midday", 35, 20, 4),
        ]

        with patch.object(
            tomorrow_forecast,
            "_load_block_rows",
            side_effect=[weekday_blocks, overall_blocks],
        ):
            result = tomorrow_forecast.get_date_forecast(
                FakeEngine(),
                "Epcot",
                "2027-10-13",
            )

        self.assertEqual("fallback", result["status"])
        self.assertEqual("overall_baseline", result["source"])
        self.assertEqual("near_typical", result["comparison"])
        self.assertEqual("low", result["confidence"]["level"])
        self.assertEqual(40, result["sample_count"])
        self.assertIn("Not enough matching Wednesday history", result["summary"])

    def test_empty_history_returns_learning_without_invented_windows(self):
        with patch.object(
            tomorrow_forecast,
            "_load_block_rows",
            side_effect=[[], []],
        ):
            result = tomorrow_forecast.get_date_forecast(
                FakeEngine(),
                "Animal Kingdom",
                "2027-10-14",
            )

        self.assertEqual("learning", result["status"])
        self.assertEqual("insufficient_data", result["source"])
        self.assertEqual([], result["blocks"])
        self.assertIsNone(result["best_window"])
        self.assertIsNone(result["peak_window"])
        self.assertEqual("low", result["confidence"]["level"])

    def test_direction_thresholds_remain_directional_not_precise_predictions(self):
        cases = {
            -15: "noticeably_quieter",
            -14: "slightly_quieter",
            -7: "slightly_quieter",
            -6: "near_typical",
            6: "near_typical",
            7: "slightly_busier",
            14: "slightly_busier",
            15: "noticeably_busier",
        }

        for difference, expected in cases.items():
            with self.subTest(difference=difference):
                self.assertEqual(
                    expected,
                    tomorrow_forecast._comparison_label(difference),
                )


if __name__ == "__main__":
    unittest.main()
