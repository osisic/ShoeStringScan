import pytest
from plugin_manager import PluginManager
from plugins.tool_plugin_base import ToolPlugin
import types

class DummyCacheManager:
    def __init__(self):
        self.checked = False
        self.pulled = False
    def is_image_cached(self, image_ref):
        self.checked = True
        return False
    def pull_image(self, image_ref):
        self.pulled = True
        return True

class DummyRuntimeExecutor:
    def __init__(self):
        self.ran = False
        self.last_args = None
    def docker_run(self, image, command, volume_map, **kwargs):
        self.ran = True
        self.last_args = (image, command, volume_map, kwargs)
        return 0

def test_scorecard_plugin_loads():
    pm = PluginManager()
    plugin = pm.get_tool("scorecard")
    assert plugin is not None
    assert plugin.NAME == "scorecard"
    assert issubclass(type(plugin), ToolPlugin)

def test_scorecard_ensure_image(monkeypatch):
    from plugins.tool_scorecard import Plugin
    cache = DummyCacheManager()
    plugin = Plugin()
    plugin.cache_manager = cache
    plugin.DOCKER_IMAGE = "dummy/image"
    plugin.DOCKER_TAG_CMD = ["scorecard", "--version"]
    plugin.ensure_image(offline=False)
    assert cache.checked
    assert cache.pulled

def test_scorecard_scan_calls_runtime(monkeypatch):
    from plugins.tool_scorecard import Plugin
    runtime = DummyRuntimeExecutor()
    plugin = Plugin()
    plugin.runtime_executor = runtime
    plugin.DOCKER_IMAGE = "dummy/image"
    plugin.scan("/tmp/repo", "/tmp/work", "1", "1g")
    assert runtime.ran

def test_scorecard_parse_results():
    from plugins.tool_scorecard import Plugin
    plugin = Plugin()
    # Simulate a minimal valid output
    raw_path = "/tmp/fake_scorecard_output.json"
    import json
    findings = [{"check": "Branch-Protection", "score": 5, "reason": "ok"}]
    with open(raw_path, "w") as f:
        json.dump(findings, f)
    results = plugin.parse_results(raw_path)
    assert isinstance(results, list)
    assert results[0]["check"] == "Branch-Protection" 