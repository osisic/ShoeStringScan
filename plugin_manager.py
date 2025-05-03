import os
import importlib.util
import sys
import logging
from plugins.tool_plugin_base import ToolPlugin

PLUGINS_PATH = os.path.join(os.path.dirname(__file__), 'plugins')

class PluginManager:
    def __init__(self, plugins_path=PLUGINS_PATH, import_base='plugins'):
        self.plugins_path = plugins_path
        self.import_base = import_base
        self._plugins = None
        self.logger = logging.getLogger("shoestring.plugin_manager")

    def available_tools(self):
        if self._plugins is not None:
            return self._plugins
        plugins = []
        if not os.path.isdir(self.plugins_path):
            self.logger.warning(f"Plugins path does not exist: {self.plugins_path}")
            return plugins
        for fname in os.listdir(self.plugins_path):
            if fname.startswith('tool_') and fname.endswith('.py') and fname != 'tool_plugin_base.py':
                mod_name = f"{self.import_base}.{fname[:-3]}"
                try:
                    self.logger.debug(f"Attempting to import plugin: {mod_name}")
                    spec = importlib.util.find_spec(mod_name)
                    if not spec:
                        self.logger.warning(f"Could not find spec for {mod_name}")
                        continue
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    if hasattr(mod, 'Plugin'):
                        plugin_cls = getattr(mod, 'Plugin')
                        if issubclass(plugin_cls, ToolPlugin):
                            plugins.append(plugin_cls())
                            self.logger.info(f"Loaded plugin: {mod_name}")
                        else:
                            self.logger.warning(f"Plugin class in {mod_name} is not a ToolPlugin subclass")
                    else:
                        self.logger.warning(f"No Plugin class in {mod_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load plugin {mod_name}: {e}")
        self.logger.info(f"Discovered {len(plugins)} plugins.")
        self._plugins = plugins
        return plugins

    def get_tool(self, name):
        for plugin in self.available_tools():
            if getattr(plugin, 'NAME', None) == name:
                self.logger.debug(f"Found tool by name: {name}")
                return plugin
        self.logger.warning(f"Tool not found: {name}")
        return None 