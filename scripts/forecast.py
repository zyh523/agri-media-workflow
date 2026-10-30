#!/usr/bin/env python3
"""Offline empirical organic-view baseline. No API calls or publishing."""

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

MATCH_FIELDS = ("platform", "account_id", "pillar", "format", "duration_bucket")
METHOD = "same_account_fixed_window_empirical_quantiles_v1"


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string with timezone")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return result


def integer(value, name, minimum=1, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return value


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def summarize(records):
    values = [r["views"] for r in records]
    return {key: round(quantile(values, p), 2)
            for key, p in (("q10", .1), ("q50", .5), ("q90", .9))}


def select(records, origin, lookback_days, max_samples):
    """Deduplicate only revisions that were actually observable at origin."""
    earliest = origin - timedelta(days=lookback_days)
    latest = {}
    for record in records:
        if not (earliest <= record["_published"] < origin):
            continue
        if record["_captured"] > origin:
            continue
        previous = latest.get(record["post_id"])
        if previous is None or record["_captured"] > previous["_captured"]:
            latest[record["post_id"]] = record
    return sorted(latest.values(), key=lambda r: (r["_published"], r["post_id"]))[-max_samples:]


def forecast(rows, target):
    if not isinstance(target, dict):
        raise ValueError("target must be a JSON object")
    for key in MATCH_FIELDS:
        if not isinstance(target.get(key), str) or not target[key].strip():
            raise ValueError(f"target.{key} must be a nonempty string")
    window = integer(target.get("window_hours"), "window_hours", maximum=8760)
    origin = timestamp(target.get("as_of"))
    days = integer(target.get("lookback_days", 60), "lookback_days", maximum=3660)
    minimum = integer(target.get("min_samples", 10), "min_samples", minimum=10)
    maximum = integer(target.get("max_samples", 100), "max_samples", maximum=10000)
    if maximum < minimum:
        raise ValueError("max_samples must be >= min_samples")
    counts = Counter()
    records = []
    seen = {}
    for row in rows:
        if not isinstance(row, dict):
            counts["not_an_object"] += 1
            continue
        if any(row.get(key) != target[key] for key in MATCH_FIELDS):
            counts["different_cohort"] += 1
            continue
        if row.get("traffic_type") != "organic":
            counts["not_confirmed_organic"] += 1
            continue
        if row.get("metric_kind") != "fixed_window":
            counts["not_fixed_window"] += 1
            continue
        if isinstance(row.get("window_hours"), bool) or row.get("window_hours") != window:
            counts["different_window"] += 1
            continue
        if not isinstance(row.get("post_id"), str) or not row["post_id"].strip():
            counts["missing_post_id"] += 1
            continue
        if row.get("views") is None:
            counts["missing_views"] += 1
            continue
        try:
            views = integer(row["views"], "views", minimum=0, maximum=10**15)
            pub = timestamp(row.get("published_at"))
            captured = timestamp(row.get("captured_at"))
            maturity = pub + timedelta(hours=window)
        except (ValueError, TypeError, OverflowError):
            counts["invalid_value_or_timestamp"] += 1
            continue
        if captured < maturity:
            counts["captured_before_window_end"] += 1
            continue
        if captured > origin or pub >= origin:
            counts["not_available_as_of"] += 1
            continue
        # Ambiguous same-time revisions must not make the result depend on row order.
        identity = (row["post_id"], captured)
        if identity in seen and seen[identity] != views:
            raise ValueError(f"conflicting views for post_id={row['post_id']} at same captured_at")
        seen[identity] = views
        records.append(dict(row, _published=pub, _captured=captured))
    selected = select(records, origin, days, maximum)
    eligible_ids = {r["post_id"] for r in selected}
    counts["old_or_beyond_sample_cap_rows"] = sum(
        r["post_id"] not in eligible_ids for r in records)
    counts["superseded_or_duplicate_rows"] = sum(
        r["post_id"] in eligible_ids for r in records) - len(selected)
    result = {
        "schema_version": 1,
        "status": "baseline_available" if len(selected) >= minimum else "insufficient_data",
        "metric": "organic_views",
        "window_hours": window,
        "as_of": target["as_of"],
        "cohort": {key: target[key] for key in MATCH_FIELDS},
        "method": METHOD,
        "min_samples": minimum,
        "lookback_days": days,
        "max_samples": maximum,
        "sample_count": len(selected),
        "sample_post_ids": [r["post_id"] for r in selected],
        "excluded_rows": dict(counts),
        "empirical_views": None,
        "backtest": None,
        "limitations": [
            "Historical empirical range; not a calibrated future probability interval.",
            "No title, thumbnail or creative-score uplift is estimated.",
            "No CTR, click count, sales or causal effect is estimated.",
            "Requires genuine fixed-window, confirmed organic account data.",
            "Seasonality, selection bias and platform/account drift remain."
        ]
    }
    if len(selected) < minimum:
        result["next_action"] = "Collect comparable fixed-window account data; do not infer views from likes."
        return result
    result["empirical_views"] = summarize(selected)
    errors, log_errors, hits, evaluated = [], [], [], []
    # Each historical prediction uses only metrics available before that post was published.
    for test in selected[-20:]:
        train = select(records, test["_published"], days, maximum)
        if len(train) < minimum:
            continue
        estimate = summarize(train)
        actual = test["views"]
        errors.append(abs(actual - estimate["q50"]))
        log_errors.append(abs(math.log1p(actual) - math.log1p(estimate["q50"])))
        hits.append(estimate["q10"] <= actual <= estimate["q90"])
        evaluated.append(test["post_id"])
    n = len(errors)
    result["backtest"] = {
        "method": "rolling_origin_observed_before_publication",
        "count": n,
        "post_ids": evaluated,
        "mae_views": round(sum(errors) / n, 2) if n else None,
        "mae_log1p": round(sum(log_errors) / n, 4) if n else None,
        "empirical_range_coverage": round(sum(hits) / n, 4) if n else None,
        "status": "descriptive_only" if n < 10 else "backtested_baseline_not_probability_guarantee"
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", required=True, help="UTF-8 fixed-window metrics JSONL")
    parser.add_argument("--target", required=True, help="UTF-8 forecast target JSON")
    parser.add_argument("--output", help="Optional output JSON; refuses to overwrite input files")
    args = parser.parse_args()
    try:
        history_path, target_path = Path(args.history), Path(args.target)
        if args.output and Path(args.output).resolve() in (history_path.resolve(), target_path.resolve()):
            raise ValueError("output must differ from input files")
        rows = []
        for number, line in enumerate(history_path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON at history line {number}: {exc.msg}") from exc
        target = json.loads(target_path.read_text(encoding="utf-8-sig"))
        output = json.dumps(forecast(rows, target), ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0
    except (ValueError, OSError, OverflowError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
