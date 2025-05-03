import sys
import os
import types
import importlib
import pytest
from plugin_manager import PluginManager
from plugins.tool_plugin_base import ToolPlugin

# Dummy plugin for testing
def make_dummy_plugin():
    class DummyPlugin(ToolPlugin):
        NAME = "dummy"
        PRIORITY = 42
        def ensure_image(self, offline): pass
        def scan(self, target, work_dir, cpu_limit, mem_limit): pass
        def parse_results(self, raw_path): pass
    return DummyPlugin

def test_plugin_manager_discovers_plugins(monkeypatch, tmp_path):
    # Use a unique package name for the test
    pkg_name = "test_plugins"
    plugins_dir = tmp_path / pkg_name
    plugins_dir.mkdir()
    (plugins_dir / "__init__.py").write_text("")  # Make it a package
    plugin_path = plugins_dir / "tool_dummy.py"
    plugin_path.write_text('''
from plugins.tool_plugin_base import ToolPlugin
class Plugin(ToolPlugin):
    NAME = "dummy"
    PRIORITY = 42
    def ensure_image(self, offline): pass
    def scan(self, target, work_dir, cpu_limit, mem_limit): pass
    def parse_results(self, raw_path): pass
''')
    sys.path.insert(0, str(tmp_path))
    pm = PluginManager(plugins_path=str(plugins_dir), import_base=pkg_name)
    tools = pm.available_tools()
    assert any(t.NAME == "dummy" for t in tools)
    sys.path.pop(0)

def test_plugin_manager_get_tool(monkeypatch):
    # Patch PluginManager to return a dummy plugin
    DummyPlugin = make_dummy_plugin()
    class DummyPM(PluginManager):
        def available_tools(self):
            return [DummyPlugin()]
    pm = DummyPM()
    tool = pm.get_tool("dummy")
    assert isinstance(tool, DummyPlugin)
    assert tool.NAME == "dummy" 