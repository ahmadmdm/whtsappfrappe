from __future__ import annotations

from pathlib import Path
import os
import signal
import subprocess
import sys
import time

from whatapp.local_service import (
	ensure_runtime_directories,
	get_runtime_binary_path,
)


RESTART_DELAY_SECONDS = 3


def load_env_file(path: Path) -> dict[str, str]:
	data: dict[str, str] = {}
	if not path.exists():
		return data
	for line in path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		value = value.strip()
		if value.startswith('"') and value.endswith('"'):
			value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
		data[key] = value
	return data


def build_process_env(env_path: Path) -> dict[str, str]:
	env = os.environ.copy()
	env.update(load_env_file(env_path))
	return env


def terminate_process(process: subprocess.Popen | None) -> None:
	if not process or process.poll() is not None:
		return
	process.terminate()
	try:
		process.wait(timeout=10)
	except subprocess.TimeoutExpired:
		process.kill()
		process.wait(timeout=5)


def main() -> int:
	site = os.environ.get("WHATAPP_SITE") or os.environ.get("SITE_NAME") or "srs.localhost"
	paths = ensure_runtime_directories(site)
	env_path = Path(paths["env_path"])
	if not env_path.exists():
		print(f"Whatapp GoWA env file is missing at {env_path}", file=sys.stderr)
		return 1

	binary_path = get_runtime_binary_path()
	if not binary_path.exists():
		print(f"Whatapp GoWA binary is missing at {binary_path}", file=sys.stderr)
		return 1

	child: subprocess.Popen | None = None
	last_env_mtime = env_path.stat().st_mtime if env_path.exists() else 0.0

	def handle_signal(signum, _frame):
		terminate_process(child)
		sys.exit(128 + signum)

	signal.signal(signal.SIGTERM, handle_signal)
	signal.signal(signal.SIGINT, handle_signal)

	while True:
		if child is None:
			child = subprocess.Popen(
				[str(binary_path), "rest"],
				cwd=str(paths["data_dir"]),
				env=build_process_env(env_path),
			)

		current_mtime = env_path.stat().st_mtime if env_path.exists() else 0.0
		if current_mtime != last_env_mtime:
			last_env_mtime = current_mtime
			terminate_process(child)
			child = None
			time.sleep(1)
			continue

		status = child.poll()
		if status is not None:
			print(f"Whatapp GoWA process exited with status {status}, restarting in {RESTART_DELAY_SECONDS}s", file=sys.stderr)
			child = None
			time.sleep(RESTART_DELAY_SECONDS)
			continue

		time.sleep(2)


if __name__ == "__main__":
	raise SystemExit(main())