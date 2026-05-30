<!-- Auto-generated guidance for AI coding agents working on oxchief-client -->
# Copilot / AI Agent Instructions — oxchief-client

Purpose: Give an AI contributor immediate, actionable context about this repository's structure, runtime patterns, dev workflows, and integration points so edits are safe and aligned with project conventions.

Key files and places to inspect
- `src/`: main Python service code. Start with [src/config.py](src/config.py) and [src/constants.py](src/constants.py).
- `src/base_station_client.py`: example of hardware integration, `asyncio` usage, `RTCMReader`, and `websockets` usage.
- `docs/`: architecture and deployment notes (read before making infra changes).
- `dockerfiles/` and `tests/`: Docker and test artifacts.
- `services/`: systemd unit files used on target devices (copy-edit only when service behavior must change).

Big-picture architecture (what matters)
- This is a Python-based client suite that runs on Raspberry Pi-like devices. Each process in `src/` is an autonomous service (e.g., `base_station_client.py`, `autopilot_client.py`).
- Services interact with hardware (serial ports, GNSS) and remote servers. Example flow: `base_station_client` reads RTCM from a serial device via `pyrtcm.RTCMReader`, encodes with `base64.b85encode`, and sends JSON over a `websockets` connection to a configured URI.
- Configuration is centralized via the `Config` class (`src/config.py`) and `config.ini` files — prefer reading and updating those rather than scattering hard-coded values.

Runtime & development workflows
- Virtualenv: a full virtualenv is committed under `env/`. Use `env/bin/python` for reproducible runs on this machine. Example: `env/bin/python src/base_station_client.py`.
- Debugging: some modules include `debugpy` support guarded by `CONFIG.enable_python_debug` — enable via configuration to attach debugger without editing source.
- Tests: there is a `tests/` directory with pytest-style tests. Run tests from repo root (if `pytest` is installed): `env/bin/python -m pytest tests`.
- Docker: multi-Dockerfile support lives in `dockerfiles/` and `tests/` (test images). Use those for containerized runs.

Project-specific conventions and patterns
- Global `CONFIG` instances: many modules import a single Config instance (`CONFIG = Config()`) at module top-level. Respect this pattern when adding new modules.
- Constants module: use `Constants` in `src/constants.py` for paths like the device list filename rather than hard-coded paths.
- Low-level hardware control: scripts and services sometimes write to `/oxpipe` to trigger host actions (reboot, restart). Avoid modifying these control scripts unless you're sure of side effects on deployed devices.
- System integration: service unit files in `services/` correspond to on-device systemd setup — changes here affect how software is started on the device.

Integration points and external dependencies
- Websocket endpoints: built from `CONFIG` values (see `URI_CORRECTION_SILENT` in `src/base_station_client.py`). Authentication is passed via headers (`jwt`).
- Serial devices: discovered by reading a devices file referenced by `Constants.DEVICES_FILENAME`; code assumes entries like `'/dev/ttyUSB0 - device_name'` (see `list_attached_devices()` and `ublox_serial_port_name_helper()`).
- OS-level control: commands that reboot or restart scripts are sent to the host via `echo "..." > /oxpipe`.

How to change code safely (AI agent rules)
- Prefer config-driven changes: update `src/config.py` or `config.ini` rather than sprinkling literals.
- When modifying hardware or system-level code (anything under `src/` that writes to `/oxpipe`, uses serial, or touches `services/`), keep changes minimal and explain assumptions in the PR.
- Tests: run `env/bin/python -m pytest tests` whenever you change logic; add focused unit tests under `tests/` for new behavior.
- Docker and CI: if adding system dependencies, update `requirements.txt` and mirror changes in relevant `dockerfiles/Dockerfile` files.

Examples (concrete snippets)
- Run base station client locally with included venv:
```
env/bin/python src/base_station_client.py
```
- Run tests:
```
env/bin/python -m pytest tests
```
- Inspect serial device lookup (device file expected format): see [src/base_station_client.py](src/base_station_client.py#L1-L200)

If unsure: open `docs/` and `src/config.py`, then ask the repo owner before changing systemd units or device-write scripts.

Feedback: I added this guidance to `.github/copilot-instructions.md`. Tell me if you'd like more detail about any service, a runbook for device deployment, or explicit test commands for CI.
