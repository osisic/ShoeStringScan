import os
import subprocess
import pytest
import shutil
from orchestrator import Orchestrator
from plugin_manager import PluginManager
from report_aggregator import ReportAggregator

WEBGOAT_REPO = "https://github.com/vulnerable-apps/WebGoat.git"
WEBGOAT_DIR = "../WebGoat"

@pytest.mark.skipif(
    not shutil.which("docker"),
    reason="Docker is not available"
)
def test_scorecard_webgoat_scan():
    # Clone WebGoat if not present
    if not os.path.isdir(WEBGOAT_DIR):
        subprocess.run(["git", "clone", WEBGOAT_REPO, WEBGOAT_DIR], check=True)
    # Prepare orchestrator
    orch = Orchestrator()
    pm = PluginManager()
    aggregator = ReportAggregator()
    # Only run scorecard
    scorecard_plugin = [p for p in pm.available_tools() if getattr(p, "NAME", None) == "scorecard"]
    assert scorecard_plugin, "Scorecard plugin not found"
    class OnlyScorecardPM(PluginManager):
        def available_tools(self):
            return scorecard_plugin
    orch.plugin_manager = OnlyScorecardPM()
    orch.report_aggregator = aggregator
    # Create a work dir
    import tempfile
    work_dir = tempfile.mkdtemp()
    # Run orchestrator
    results = orch.run(target=WEBGOAT_DIR, work_dir=work_dir, threads=1)
    # Check that findings are present
    assert isinstance(results, dict)
    found = False
    for tool_result in results.get("findings", []):
        if tool_result.get("tool") == "scorecard" and tool_result.get("findings"):
            found = True
    assert found, "No findings produced by Scorecard on WebGoat" 