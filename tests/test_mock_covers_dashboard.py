"""Verify the mock GB10 exporter still covers every metric the dashboard queries.

If someone edits dashboard PromQL and the mock exporter drifts, the no-hardware
preview silently loses panels. This guard re-parses all dashboard `expr`s and
asserts the mock exporter's output contains every queried metric name.

Run:  python3 tests/test_mock_covers_dashboard.py        (no pytest needed)
"""
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import mock_gb10_metrics as mock  # noqa: E402

DASH = REPO / "grafana/provisioning/dashboards/dgx-spark-cluster.json"

# metric immediately followed by '{' — the canonical PromQL metric selector.
METRIC_SELECTOR = re.compile(r"([A-Za-z_:][A-Za-z0-9_:]*)\s*(?=\{)")
# vllm series can appear bare (e.g. avg(vllm:kv_cache_usage_perc))
VLLM_BARE = re.compile(r"(?<![\w:.])(vllm:[a-z0-9_]+)")


def dashboard_metrics() -> dict[str, list[str]]:
    """metric name -> panels that query it."""
    data = json.loads(DASH.read_text(encoding="utf-8"))
    seen: dict[str, list[str]] = {}
    for panel in data.get("panels", []):
        label = panel.get("title") or str(panel.get("id"))
        for target in panel.get("targets", []) or []:
            expr = str(target.get("expr", ""))
            if not expr:
                continue
            for metric in METRIC_SELECTOR.findall(expr):
                seen.setdefault(metric, []).append(label)
            for metric in VLLM_BARE.findall(expr):
                seen.setdefault(metric, []).append(label)
    return seen


def mock_metrics() -> set[str]:
    out = mock.render()
    return set(re.findall(r"^([A-Za-z_:][A-Za-z0-9_:]*)\{", out, re.M))


class MockCoversDashboardTests(unittest.TestCase):
    def test_every_dashboard_metric_is_produced_by_mock(self):
        produced = mock_metrics()
        missing = {m: p for m, p in dashboard_metrics().items() if m not in produced}
        self.assertEqual(
            missing,
            {},
            "mock exporter no longer covers dashboard metrics (missing: %s)" % missing,
        )

    def test_mock_marks_itself_mock(self):
        produced = mock_metrics()
        self.assertIn("mock_gb10_info", produced)

    def test_dashboard_not_empty(self):
        data = json.loads(DASH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data.get("panels", [])), 17)
        self.assertGreaterEqual(len(dashboard_metrics()), 14)


if __name__ == "__main__":
    unittest.main()
