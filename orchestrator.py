import logging
import concurrent.futures
import os
import subprocess

class Orchestrator:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("shoestring.orchestrator")
        self.logger.debug({
            "event": "orchestrator_init",
            "args": args,
            "kwargs": kwargs
        })
        self.plugin_manager = kwargs.get("plugin_manager")
        self.report_aggregator = kwargs.get("report_aggregator")

    def docker_prune(self):
        self.logger.info({"event": "docker_cleanup_start"})
        try:
            subprocess.run(["docker", "system", "prune", "-f"], check=False)
            self.logger.info({"event": "docker_cleanup_complete"})
        except Exception as e:
            self.logger.error({"event": "docker_cleanup_error", "error": str(e)})

    def run(self, target, work_dir, threads=1, **kwargs):
        # Use injected or default plugin manager and aggregator
        pm = self.plugin_manager
        if pm is None:
            from plugin_manager import PluginManager
            pm = PluginManager()
        aggregator = self.report_aggregator
        if aggregator is None:
            from report_aggregator import ReportAggregator
            aggregator = ReportAggregator()
        self.logger.info({
            "event": "orchestrator_run_called",
            "target": target,
            "work_dir": work_dir,
            "threads": threads
        })
        tools = pm.available_tools()
        results = []
        def run_tool(tool):
            try:
                tool.ensure_image(offline=False)
                tool.scan(target, work_dir, tool.DEFAULT_CPU, tool.DEFAULT_MEM)
                raw_path = os.path.join(work_dir, "scorecard.json")
                findings = tool.parse_results(raw_path)
                return {"tool": tool.NAME, "findings": findings}
            except Exception as e:
                self.logger.error({"event": "tool_error", "tool": getattr(tool, 'NAME', None), "error": str(e)})
                return {"tool": getattr(tool, 'NAME', None), "error": str(e)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futs = [executor.submit(run_tool, tool) for tool in tools]
            for fut in concurrent.futures.as_completed(futs):
                results.append(fut.result())
        summary = aggregator.aggregate(results)
        self.logger.info({"event": "orchestrator_run_complete", "summary": summary})
        # Deliver output here (write to file, return, etc.)
        # Optional: Clean up Docker
        self.docker_prune()
        return summary 