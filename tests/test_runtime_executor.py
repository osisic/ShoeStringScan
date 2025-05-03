import os
import tempfile
import pytest
from runtime_executor import RuntimeExecutor
from plugins.tool_plugin_base import ToolScanError
import logging
from dotenv import load_dotenv
import json
from datetime import datetime

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
    assert result == "hello-shoestring\n"

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
    assert result == ""
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

def test_docker_run_logs_success(monkeypatch, caplog):
    re = RuntimeExecutor()
    caplog.set_level(logging.INFO)
    result = re.docker_run(
        image="busybox",
        command=["echo", "log-success"],
        volume_map={},
        work_dir="/",
        cpu_limit="0.5",
        mem_limit="128m"
    )
    assert "log-success" in caplog.text
    assert result == "log-success\n"

def test_docker_run_logs_error(monkeypatch, caplog):
    re = RuntimeExecutor()
    caplog.set_level(logging.ERROR)
    with pytest.raises(ToolScanError):
        re.docker_run(
            image="busybox",
            command=["sh", "-c", "echo error-message 1>&2; exit 42"],
            volume_map={},
            work_dir="/",
            cpu_limit="0.5",
            mem_limit="128m"
        )
    assert "error-message" in caplog.text
    assert "exit code 42" in caplog.text

def test_docker_run_with_logs_success(monkeypatch, caplog):
    re = RuntimeExecutor()
    caplog.set_level(logging.INFO)
    output, logs = re.docker_run_with_logs(
        image="busybox",
        command=["echo", "log-success"],
        volume_map={},
        work_dir="/",
        cpu_limit="0.5",
        mem_limit="128m"
    )
    assert "log-success" in output
    assert "log-success" in logs

def test_docker_run_with_logs_error(monkeypatch, caplog):
    re = RuntimeExecutor()
    caplog.set_level(logging.ERROR)
    with pytest.raises(ToolScanError):
        output, logs = re.docker_run_with_logs(
            image="busybox",
            command=["sh", "-c", "echo error-message 1>&2; exit 42"],
            volume_map={},
            work_dir="/",
            cpu_limit="0.5",
            mem_limit="128m"
        )
    assert "error-message" in caplog.text or "error-message" in logs
    assert "exit code 42" in caplog.text or "exit code 42" in logs

def save_scorecard_result(target, start_time, output, logs, error=None):
    os.makedirs("results", exist_ok=True)
    filename = f"results/scorecard_{start_time.replace(':', '-')}_{target.split('/')[-1]}.json"
    result_data = {
        "target": target,
        "start_time": start_time,
        "output": output,
        "logs": logs,
        "error": error,
    }
    with open(filename, "w") as f:
        json.dump(result_data, f, indent=2)
    return filename

def test_scorecard_logs_github_token_error():
    re = RuntimeExecutor()
    # Do NOT set GITHUB_AUTH_TOKEN in env
    output, logs = re.docker_run_with_logs(
        image="gcr.io/openssf/scorecard",
        command=["--repo", "https://github.com/vulnerable-apps/WebGoat", "--format", "json"],
        volume_map={},
        work_dir="/",
        cpu_limit="1",
        mem_limit="1g",
        env={}  # No token
    )
    assert "GitHub token env var is not set" in logs or "GitHub token env var is not set" in output 

def test_scorecard_logs_github_token_present():
    load_dotenv()
    github_token = os.environ.get("GITHUB_AUTH_TOKEN")
    assert github_token, "GITHUB_AUTH_TOKEN must be set in .env for this test"

    re = RuntimeExecutor()
    target_repo = "https://github.com/vulnerable-apps/WebGoat"
    start_time = datetime.utcnow().isoformat()
    output = logs = error = None
    try:
        output, logs = re.docker_run_with_logs(
            image="gcr.io/openssf/scorecard",
            command=["--repo", target_repo, "--format", "json"],
            volume_map={},
            work_dir="/",
            cpu_limit="1",
            mem_limit="1g",
            env={"GITHUB_AUTH_TOKEN": github_token}
        )
    except ToolScanError as e:
        error = str(e)
        assert "GitHub token env var is not set" not in str(e)
    save_scorecard_result(target_repo, start_time, output, logs, error) 