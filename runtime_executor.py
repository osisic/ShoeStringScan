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
                # Log each line of output as error for better testability
                for line in output_lines:
                    self.logger.error(line.rstrip())
                raise ToolScanError(f"Docker run failed with exit code {proc.returncode}. Output:\n{output}")
            return output
        except subprocess.TimeoutExpired:
            proc.kill()
            self.logger.error("Docker run timed out")
            raise ToolScanError("Docker run timed out")
        except Exception as e:
            self.logger.error(f"Docker run error: {e}")
            raise ToolScanError(f"Docker run error: {e}")

    def docker_run_with_logs(self, image, command, volume_map, work_dir="/scan", cpu_limit="1", mem_limit="1g", env=None, timeout=None):
        import uuid
        container_name = f"shoestring_{uuid.uuid4().hex[:8]}"
        docker_cmd = [
            "docker", "run", "-d", "--name", container_name,
            "-w", work_dir,
            "--cpus", str(cpu_limit),
            "--memory", str(mem_limit)
        ]
        for host_path, container_path in volume_map.items():
            docker_cmd += ["-v", f"{os.path.abspath(host_path)}:{container_path}"]
        if env:
            for k, v in env.items():
                docker_cmd += ["-e", f"{k}={v}"]
        docker_cmd.append(image)
        docker_cmd += command
        self.logger.info({
            "event": "docker_run_with_logs_called",
            "cmd": docker_cmd
        })
        container_id = None
        try:
            # Start container in detached mode
            proc = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                self.logger.error(f"Failed to start container: {proc.stderr}")
                raise ToolScanError(f"Failed to start container: {proc.stderr}")
            container_id = proc.stdout.strip()
            # Wait for container to finish
            wait_cmd = ["docker", "wait", container_id]
            wait_proc = subprocess.run(wait_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
            exit_code = int(wait_proc.stdout.strip()) if wait_proc.returncode == 0 else -1
            # Get logs
            logs_cmd = ["docker", "logs", container_id]
            logs_proc = subprocess.run(logs_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            logs = logs_proc.stdout
            # Get output (simulate process output as logs for detached mode)
            output = logs
            if exit_code != 0:
                self.logger.error(f"Docker run failed with exit code {exit_code}. Logs:\n{logs}")
                for line in logs.splitlines():
                    self.logger.error(line)
                raise ToolScanError(f"Docker run failed with exit code {exit_code}. Logs:\n{logs}")
            return output, logs
        except subprocess.TimeoutExpired:
            self.logger.error("Docker run timed out")
            raise ToolScanError("Docker run timed out")
        except Exception as e:
            self.logger.error(f"Docker run error: {e}")
            raise ToolScanError(f"Docker run error: {e}")
        finally:
            if container_id:
                subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE) 