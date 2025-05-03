# Shoestring Code Scanner

A modular, cross-platform, incremental code-repository security scanner. Integrates open-source CLI scanners (Scorecard, Gitleaks, Syft, Grype, etc.) via Docker, with rich progress bars and HTML reporting.

## Features
- One-command security baseline for any Git repo
- Plug-in architecture for easy tool addition
- Offline scanning after first install (caches Docker images)
- Friendly UX: progress bars, summaries, HTML dashboard yyy


## Usage
```sh
python code_scan.py --target /path/to/repo
```

See `--help` for all options.

## Directory Structure
- `code_scan.py` – CLI entrypoint
- `orchestrator.py` – Orchestrates scan execution
- `plugin_manager.py` – Discovers and loads tool plugins
- `runtime_executor.py` – Runs Docker containers
- `cache_manager.py` – Manages Docker image cache
- `report_aggregator.py` – Aggregates and writes reports
- `plugins/` – Tool plug-ins (one per scanner)
- `templates/`, `static/` – HTML report assets
- `tests/` – Unit and integration tests

## Requirements
- Python 3.10+
- Docker 24+
- [rich](https://github.com/Textualize/rich), [PyYAML](https://pyyaml.org/), [jinja2](https://palletsprojects.com/p/jinja/)

## License
MIT 