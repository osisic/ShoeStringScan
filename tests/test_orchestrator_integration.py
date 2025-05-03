import tempfile
import os
import pytest
from orchestrator import Orchestrator
from plugin_manager import PluginManager
from plugins.tool_scorecard import Plugin as ScorecardPlugin
from report_aggregator import ReportAggregator

class DummyScorecardPlugin(ScorecardPlugin):
    def ensure_image(self, offline):
        self.image_ensured = True
    def scan(self, target, work_dir, cpu_limit, mem_limit):
        self.scanned = (target, work_dir, cpu_limit, mem_limit)
        # Write a dummy output file
        out_path = os.path.join(work_dir, "scorecard.json")
        with open(out_path, "w") as f:
            import json
            json.dump([{"check": "Branch-Protection", "score": 5, "reason": "ok"}], f)
    def parse_results(self, raw_path):
        with open(raw_path) as f:
            import json
            return json.load(f)

def test_orchestrator_runs_scorecard(monkeypatch, tmp_path):
    # Patch PluginManager to only return our dummy plugin
    class DummyPM(PluginManager):
        def available_tools(self):
            return [DummyScorecardPlugin()]
    # Patch ReportAggregator to just return the findings
    class DummyAggregator(ReportAggregator):
        def aggregate(self, tool_results):
            return {"findings": tool_results}
    # Prepare orchestrator
    orch = Orchestrator()
    orch.plugin_manager = DummyPM()
    orch.report_aggregator = DummyAggregator()
    # Run orchestrator
    target = tmp_path / "repo"
    target.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    results = orch.run(target=str(target), work_dir=str(work_dir), threads=1)
    assert "findings" in results
    assert isinstance(results["findings"], list) 