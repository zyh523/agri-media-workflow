#!/usr/bin/env python3
"""Deterministic synthetic checks: no account connection or network access."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forecast import forecast


def fixture(n=35):
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    target = dict(platform="douyin", account_id="synthetic-account", pillar="balcony",
                  format="video", duration_bucket="30-60s", window_hours=24,
                  as_of="2026-10-30T00:00:00+00:00", lookback_days=90)
    rows = []
    for i in range(n):
        pub = start + timedelta(days=i)
        rows.append(dict(post_id=f"synthetic-{i:02}",
                         **{k: target[k] for k in ("platform", "account_id", "pillar", "format", "duration_bucket")},
                         traffic_type="organic", metric_kind="fixed_window", window_hours=24,
                         published_at=pub.isoformat(),
                         captured_at=(pub + timedelta(hours=24)).isoformat(), views=100))
    return rows, target


class ForecastChecks(unittest.TestCase):
    def test_cold_start_has_no_numbers(self):
        rows, target = fixture(9)
        result = forecast(rows, target)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["empirical_views"])

    def test_known_constant_baseline_and_backtest(self):
        rows, target = fixture()
        result = forecast(rows, target)
        self.assertEqual(result["empirical_views"], dict(q10=100, q50=100, q90=100))
        self.assertEqual(result["backtest"]["mae_views"], 0)
        self.assertEqual(result["backtest"]["empirical_range_coverage"], 1)
        self.assertEqual(result["backtest"]["count"], 20)

    def test_paid_other_accounts_future_missing_and_immature_excluded(self):
        rows, target = fixture(10)
        changes = [dict(traffic_type="paid"), dict(account_id="other"),
                   dict(captured_at="2027-01-01T00:00:00+00:00"), dict(views=None),
                   dict(captured_at=rows[0]["published_at"]), dict(metric_kind="lifetime_snapshot"),
                   dict(views=True), dict(views=-1), dict(window_hours=72)]
        for i, change in enumerate(changes):
            rows.append(dict(rows[0], post_id=f"bad-{i}", **change))
        result = forecast(rows, target)
        self.assertEqual(result["sample_count"], 10)
        self.assertEqual(result["empirical_views"]["q50"], 100)

    def test_zero_is_not_missing_and_duplicate_not_double_counted(self):
        rows, target = fixture(10)
        for row in rows:
            row["views"] = 0
        result = forecast(rows + [copy.deepcopy(rows[0])], target)
        self.assertEqual(result["sample_count"], 10)
        self.assertEqual(result["empirical_views"]["q50"], 0)

    def test_no_future_revision_leaks_into_backtest(self):
        rows, target = fixture()
        revised = dict(rows[0], captured_at="2026-10-29T00:00:00+00:00", views=999999)
        result = forecast(rows + [revised], target)
        self.assertEqual(result["backtest"]["mae_views"], 0)

    def test_timezone_required(self):
        rows, target = fixture()
        target["as_of"] = "2026-10-30T12:00:00"
        with self.assertRaises(ValueError):
            forecast(rows, target)

    def test_conflicting_same_time_revisions_rejected(self):
        rows, target = fixture()
        with self.assertRaises(ValueError):
            forecast(rows + [dict(rows[0], views=200)], target)

    def test_old_samples_not_used(self):
        rows, target = fixture()
        target["lookback_days"] = 1
        self.assertEqual(forecast(rows, target)["status"], "insufficient_data")

    def test_asymmetric_distribution_and_outlier_retained(self):
        rows, target = fixture(10)
        for i, row in enumerate(rows):
            row["views"] = i
        self.assertEqual(forecast(rows, target)["empirical_views"],
                         dict(q10=.9, q50=4.5, q90=8.1))
        for row in rows:
            row["views"] = 0
        rows[-1]["views"] = 10000
        result = forecast(rows, target)
        self.assertEqual(result["sample_count"], 10)
        self.assertEqual(result["empirical_views"]["q90"], 1000)

    def test_cli_cold_start_outputs_json_without_input_mutation(self):
        _, target = fixture()
        script = Path(__file__).with_name("forecast.py")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            history = base / "history.jsonl"
            config = base / "target.json"
            output = base / "output.json"
            history.write_text("", encoding="utf-8")
            config.write_text(json.dumps(target), encoding="utf-8")
            process = subprocess.run([sys.executable, "-X", "utf8", str(script),
                                      "--history", str(history), "--target", str(config),
                                      "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"],
                             "insufficient_data")
            self.assertEqual(history.read_text(encoding="utf-8"), "")

    def test_cli_refuses_to_overwrite_input(self):
        rows, target = fixture(1)
        script = Path(__file__).with_name("forecast.py")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            history = base / "history.jsonl"
            config = base / "target.json"
            original = json.dumps(rows[0]) + "\n"
            history.write_text(original, encoding="utf-8")
            config.write_text(json.dumps(target), encoding="utf-8")
            process = subprocess.run([sys.executable, "-X", "utf8", str(script),
                                      "--history", str(history), "--target", str(config),
                                      "--output", str(history)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(history.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
