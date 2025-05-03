import os
import tempfile
import pytest
from runtime_executor import RuntimeExecutor
from plugins.tool_plugin_base import ToolScanError

def test_docker_run_echo():
    re = RuntimeExecutor()
    # Use the official busybox image for a simple echo
    out_dir = tempfile.mkdtemp()
    result = re.docker_run(
        image="busybox",
        command=["echo", "hello-shoestring"],
        volume_map={out_dir: "/out"},
        work_dir="/out",
        cpu_limit="0.5",
        mem_limit="128m"
    )
    assert result == 0

def test_docker_run_output_capture(tmp_path):
    re = RuntimeExecutor()
    # Write a file in the container and check it appears on the host
    host_dir = tmp_path / "out"
    host_dir.mkdir()
    result = re.docker_run(
        image="busybox",
        command=["sh", "-c", "echo test > /out/hello.txt"],
        volume_map={str(host_dir): "/out"},
        work_dir="/out",
        cpu_limit="0.5",
        mem_limit="128m"
    )
    assert result == 0
    with open(host_dir / "hello.txt") as f:
        assert f.read().strip() == "test"

def test_docker_run_nonzero_exit():
    re = RuntimeExecutor()
    with pytest.raises(ToolScanError):
        re.docker_run(
            image="busybox",
            command=["sh", "-c", "exit 42"],
            volume_map={},
            work_dir="/",
            cpu_limit="0.5",
            mem_limit="128m"
        ) 