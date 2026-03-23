from __future__ import annotations

from pathlib import Path
import json
import os
import platform
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import shutil
import stat
import zipfile

import frappe


LOCAL_SERVICE_HOST = "127.0.0.1"
LOCAL_SERVICE_PORT = 8000
DEFAULT_SERVICE_URL = f"http://{LOCAL_SERVICE_HOST}:{LOCAL_SERVICE_PORT}"
LOCAL_RELEASE_VERSION = "8.3.3"
LOCAL_RELEASE_BASE_URL = "https://github.com/aldinokemal/go-whatsapp-web-multidevice/releases/download"

PLATFORM_ASSET_MAP = {
	("linux", "x86_64"): "linux_amd64",
	("linux", "amd64"): "linux_amd64",
	("linux", "aarch64"): "linux_arm64",
	("linux", "arm64"): "linux_arm64",
	("darwin", "x86_64"): "darwin_amd64",
	("darwin", "amd64"): "darwin_amd64",
	("darwin", "arm64"): "darwin_arm64",
	("darwin", "aarch64"): "darwin_arm64",
}


def get_release_asset_name() -> str:
	system = platform.system().lower()
	machine = platform.machine().lower()
	target = PLATFORM_ASSET_MAP.get((system, machine))
	if not target:
		raise RuntimeError(f"Unsupported platform for bundled GoWA setup: {system}/{machine}")
	return f"whatsapp_{LOCAL_RELEASE_VERSION}_{target}.zip"


def get_release_url() -> str:
	asset = get_release_asset_name()
	return f"{LOCAL_RELEASE_BASE_URL}/v{LOCAL_RELEASE_VERSION}/{asset}"


def get_app_root() -> Path:
	return Path(__file__).resolve().parents[1]


def get_runtime_root() -> Path:
	return get_app_root() / ".local" / "gowa"


def get_bench_root() -> Path:
	return get_app_root().parents[1]


def resolve_site_name(site: str | None = None) -> str:
	if site:
		return site

	frappe_site = getattr(frappe.local, "site", None)
	if frappe_site:
		return frappe_site

	for env_var in ("WHATAPP_SITE", "SITE_NAME"):
		value = (os.environ.get(env_var) or "").strip()
		if value:
			return value

	sites_root = get_bench_root() / "sites"
	default_site = sites_root / "currentsite.txt"
	if default_site.exists():
		value = default_site.read_text(encoding="utf-8").strip()
		if value:
			return value

	common_site_config = sites_root / "common_site_config.json"
	if common_site_config.exists():
		try:
			config = json.loads(common_site_config.read_text(encoding="utf-8"))
		except Exception:
			config = {}
		default_value = (config.get("default_site") or "").strip() if isinstance(config, dict) else ""
		if default_value:
			return default_value

	candidates = sorted(
		path.name
		for path in sites_root.iterdir()
		if path.is_dir() and (path / "site_config.json").exists()
	)
	if len(candidates) == 1:
		return candidates[0]

	raise RuntimeError("Could not determine the active site. Set WHATAPP_SITE or SITE_NAME.")


def get_runtime_binary_path() -> Path:
	return get_runtime_root() / "bin" / "whatsapp"


def get_runtime_env_path(site: str | None = None) -> Path:
	selected_site = resolve_site_name(site)
	if getattr(frappe.local, "site", None):
		return Path(frappe.get_site_path("private", "whatapp", f"gowa-{selected_site}.env"))
	return get_bench_root() / "sites" / selected_site / "private" / "whatapp" / f"gowa-{selected_site}.env"


def ensure_runtime_directories(site: str | None = None) -> dict[str, Path]:
	runtime_root = get_runtime_root()
	paths = {
		"runtime_root": runtime_root,
		"bin_dir": runtime_root / "bin",
		"data_dir": runtime_root / "data",
		"storages_dir": runtime_root / "data" / "storages",
		"statics_dir": runtime_root / "data" / "statics",
		"env_path": get_runtime_env_path(site),
	}
	for key, path in paths.items():
		if key == "env_path":
			path.parent.mkdir(parents=True, exist_ok=True)
		else:
			path.mkdir(parents=True, exist_ok=True)
	return paths


def _quote_env(value: str) -> str:
	return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _build_basic_auth(doc) -> str:
	username = (doc.basic_auth_username or "").strip()
	password = (doc.get_password("basic_auth_password", raise_exception=False) or "").strip()
	if not username or not password:
		return ""
	return f"{username}:{password}"


def build_runtime_env(doc) -> dict[str, str]:
	service_url = (doc.service_url or "").strip() or DEFAULT_SERVICE_URL
	port = LOCAL_SERVICE_PORT
	host = LOCAL_SERVICE_HOST
	if service_url.startswith("http://") or service_url.startswith("https://"):
		from urllib.parse import urlparse

		parsed = urlparse(service_url)
		if parsed.hostname:
			host = parsed.hostname
		if parsed.port:
			port = parsed.port

	basic_auth = _build_basic_auth(doc)
	webhook_url = f"{frappe.utils.get_url()}/api/method/whatapp.api.receive_webhook"
	webhook_secret = (doc.get_password("webhook_secret", raise_exception=False) or "").strip()
	webhook_events = (doc.webhook_events or "").strip()

	env = {
		"APP_HOST": host,
		"APP_PORT": str(port),
		"APP_DEBUG": "false",
		"APP_OS": "Whatapp",
		"WHATSAPP_ACCOUNT_VALIDATION": "false",
		"WHATSAPP_WEBHOOK": webhook_url,
		"WHATSAPP_AUTO_MARK_READ": "false",
		"WHATSAPP_AUTO_DOWNLOAD_MEDIA": "true",
	}
	if basic_auth:
		env["APP_BASIC_AUTH"] = basic_auth
	if webhook_secret:
		env["WHATSAPP_WEBHOOK_SECRET"] = webhook_secret
	if webhook_events:
		env["WHATSAPP_WEBHOOK_EVENTS"] = webhook_events
	return env


def sync_local_service_config(doc=None, site: str | None = None) -> str:
	if doc is None:
		doc = frappe.get_single("Whatapp Settings")
	paths = ensure_runtime_directories(site)
	env = build_runtime_env(doc)
	lines = [f"{key}={_quote_env(value)}" for key, value in sorted(env.items())]
	content = "\n".join(lines) + "\n"
	paths["env_path"].write_text(content, encoding="utf-8")
	return str(paths["env_path"])


def install_local_binary(force: bool = False) -> str:
	paths = ensure_runtime_directories()
	binary_path = get_runtime_binary_path()
	if binary_path.exists() and not force:
		return str(binary_path)
	asset_name = get_release_asset_name()
	release_url = get_release_url()

	with TemporaryDirectory(prefix="whatapp-gowa-") as tmpdir:
		archive_path = Path(tmpdir) / asset_name
		with urlopen(release_url) as response, archive_path.open("wb") as output:
			shutil.copyfileobj(response, output)

		with zipfile.ZipFile(archive_path) as archive:
			members = [name for name in archive.namelist() if not name.endswith("/")]
			binary_member = next((name for name in members if "/" not in name and not name.lower().endswith(".md")), None)
			if not binary_member:
				raise FileNotFoundError(f"Could not find GoWA binary inside {asset_name}")
			extracted_path = Path(archive.extract(binary_member, path=paths["bin_dir"]))
			if extracted_path != binary_path:
				extracted_path.replace(binary_path)

	binary_path.chmod(binary_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
	return str(binary_path)


def ensure_local_service_ready(doc=None, site: str | None = None) -> dict[str, str | bool]:
	if doc is None and getattr(frappe.local, "site", None):
		doc = frappe.get_single("Whatapp Settings")

	env_path = sync_local_service_config(doc, site) if doc is not None else str(ensure_runtime_directories(site)["env_path"])
	binary_path = install_local_binary(force=False)
	return {"ok": True, "binary_path": binary_path, "env_path": env_path}