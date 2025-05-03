import logging
import subprocess
import shlex
import os
from plugins.tool_plugin_base import ToolScanError

class RuntimeExecutor:
    def __init__(self):
        self.logger = logging.getLogger("shoestring.runtime_executor")
        self.logger.debug({"event": "runtime_executor_init"})

    def docker_run(self, image, command, volume_map, work_dir="/scan", cpu_limit="1", mem_limit="1g", env=None, timeout=None):
        # Build docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "-w", work_dir,
            "--cpus", str(cpu_limit),
            "--memory", str(mem_limit)
        ]
        # Mount volumes
        for host_path, container_path in volume_map.items():
            docker_cmd += ["-v", f"{os.path.abspath(host_path)}:{container_path}"]
        # Set env vars
        if env:
            for k, v in env.items():
                docker_cmd += ["-e", f"{k}={v}"]
        docker_cmd.append(image)
        docker_cmd += command
        self.logger.info({
            "event": "docker_run_called",
            "cmd": docker_cmd
        })
        try:
            proc = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            output_lines = []
            for line in proc.stdout:
                self.logger.info(line.rstrip())
                output_lines.append(line)
            proc.wait(timeout=timeout)
            output = ''.join(output_lines)
            if proc.returncode != 0:
                self.logger.error(f"Docker run failed with exit code {proc.returncode}. Output:\n{output}")
                raise ToolScanError(f"Docker run failed with exit code {proc.returncode}. Output:\n{output}")
            return output
        except subprocess.TimeoutExpired:
            proc.kill()
            raise ToolScanError("Docker run timed out")
        except Exception as e:
            raise ToolScanError(f"Docker run error: {e}") 