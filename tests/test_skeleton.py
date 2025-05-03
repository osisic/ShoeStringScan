import pytest
from orchestrator import Orchestrator
from plugin_manager import PluginManager

def test_orchestrator_init():
    orch = Orchestrator()
    assert orch is not None

def test_plugin_manager_init():
    pm = PluginManager()
    assert pm is not None
    tools = pm.available_tools()
    assert isinstance(tools, list)
    assert any(getattr(t, "NAME", None) == "scorecard" for t in tools) 