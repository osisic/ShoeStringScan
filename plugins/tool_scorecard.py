import json
import os
import logging
from dotenv import load_dotenv
from plugins.tool_plugin_base import ToolPlugin, ToolInstallError, ToolScanError, ToolParseError

load_dotenv()

class Plugin(ToolPlugin):
    NAME = "scorecard"
    PRIORITY = 10
    DEFAULT_CPU = "1"
    DEFAULT_MEM = "1g"
    DOCKER_IMAGE = "gcr.io/openssf/scorecard"
    DOCKER_TAG_CMD = ["--version"]
    WEBGOAT_GITHUB_URL = "https://github.com/vulnerable-apps/WebGoat"

    def __init__(self):
        # Allow injection for testing
        try:
            from cache_manager import CacheManager
            from runtime_executor import RuntimeExecutor
            self.cache_manager = CacheManager()
            self.runtime_executor = RuntimeExecutor()
        except ImportError:
            self.cache_manager = None
            self.runtime_executor = None
        self.logger = logging.getLogger("shoestring.scorecard_plugin")
        self.last_stdout = None

    def ensure_image(self, offline):
        cm = getattr(self, 'cache_manager', None)
        if cm is None:
            from cache_manager import CacheManager
            cm = CacheManager()
        if not cm.is_image_cached(self.DOCKER_IMAGE):
            if offline:
                raise ToolInstallError("Image not cached and offline mode enabled")
            cm.pull_image(self.DOCKER_IMAGE)

    def scan(self, target, work_dir, cpu_limit, mem_limit):
        re = getattr(self, 'runtime_executor', None)
        if re is None:
            from runtime_executor import RuntimeExecutor
            re = RuntimeExecutor()
        # Use GitHub URL for WebGoat, else local path
        repo_arg = self.WEBGOAT_GITHUB_URL if "WebGoat" in os.path.basename(str(target)) else "/scan"
        volume_map = {work_dir: "/out"}
        if not repo_arg.startswith("http"):
            volume_map[target] = "/scan"
        # Pass GitHub token if present
        github_token = os.environ.get("GITHUB_AUTH_TOKEN")
        env_vars = {}
        if github_token:
            env_vars["GITHUB_AUTH_TOKEN"] = github_token
        try:
            self.last_stdout = re.docker_run(
                self.DOCKER_IMAGE,
                ["--repo", repo_arg, "--format", "json", "--output", "/out/scorecard.json"],
                volume_map,
                work_dir="/scan" if not repo_arg.startswith("http") else "/",
                cpu_limit=cpu_limit,
                mem_limit=mem_limit,
                env=env_vars
            )
        except ToolScanError as e:
            self.logger.error(f"Scorecard Docker run failed: {e}")
            if self.last_stdout:
                self.logger.error(f"Scorecard container output:\n{self.last_stdout}")
            raise
        except Exception as e:
            self.logger.error(f"Scorecard Docker run error: {e}")
            raise

    def parse_results(self, raw_path):
        if not os.path.exists(raw_path):
            self.logger.error(f"Scorecard output file not found: {raw_path}")
            # Try to parse from last_stdout if available
            if self.last_stdout:
                try:
                    return json.loads(self.last_stdout)
                except Exception as e:
                    self.logger.error(f"Failed to parse Scorecard JSON from stdout: {e}")
            raise ToolParseError(f"File not found: {raw_path}")
        with open(raw_path) as f:
            data = json.load(f)
        return data 