from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

import frappe
from frappe import _


class WhatappServiceError(frappe.ValidationError):
	pass


DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


@dataclass
class WhatappConnectionSettings:
	service_url: str
	basic_auth_username: str | None
	basic_auth_password: str | None
	default_device_id: str | None
	request_timeout: int


def get_settings_doc():
	return frappe.get_single("Whatapp Settings")


def get_optional_password(doc, fieldname: str) -> str | None:
	try:
		return (doc.get_password(fieldname, raise_exception=False) or "").strip() or None
	except Exception:
		return None


def get_connection_settings() -> WhatappConnectionSettings:
	doc = get_settings_doc()
	return WhatappConnectionSettings(
		service_url=(doc.service_url or "").strip().rstrip("/"),
		basic_auth_username=(doc.basic_auth_username or "").strip() or None,
		basic_auth_password=get_optional_password(doc, "basic_auth_password"),
		default_device_id=(doc.default_device_id or "").strip() or None,
		request_timeout=max(int(doc.request_timeout or 45), 5),
	)


def require_service_url() -> WhatappConnectionSettings:
	settings = get_connection_settings()
	if not settings.service_url:
		frappe.throw("Set the service URL first in Whatapp Settings.")
	return settings


def join_url(base: str, path: str) -> str:
	return f"{base.rstrip('/')}/{path.lstrip('/')}"


def unwrap_response(payload: Any) -> Any:
	if not isinstance(payload, dict):
		return payload
	if "results" in payload:
		return payload["results"]
	return payload


def sanitize_device_id(device_id: str | None, label: str = "Device ID", *, allow_empty: bool = True) -> str | None:
	value = (device_id or "").strip()
	if not value:
		return None if allow_empty else ""
	if not DEVICE_ID_PATTERN.fullmatch(value):
		frappe.throw(
			_("{0} can only contain English letters, numbers, dots, hyphens, underscores, and colons.").format(
				_(label)
			)
		)
	return value


def request_service(
	method: str,
	path: str,
	*,
	params: dict[str, Any] | None = None,
	json_data: dict[str, Any] | None = None,
	device_id: str | None = None,
	timeout: int | None = None,
) -> Any:
	settings = require_service_url()
	headers = {"Accept": "application/json"}
	selected_device = sanitize_device_id(device_id or settings.default_device_id, allow_empty=True)
	if selected_device:
		headers["X-Device-Id"] = selected_device

	auth = None
	if settings.basic_auth_username and settings.basic_auth_password:
		auth = HTTPBasicAuth(settings.basic_auth_username, settings.basic_auth_password)

	url = join_url(settings.service_url, path)
	try:
		response = requests.request(
			method=method.upper(),
			url=url,
			params=params,
			json=json_data,
			headers=headers,
			auth=auth,
			timeout=timeout or settings.request_timeout,
		)
	except requests.RequestException as exc:
		raise WhatappServiceError(f"Could not reach Whatapp service: {exc}") from exc

	try:
		payload = response.json()
	except ValueError:
		payload = {"message": response.text}

	if response.status_code >= 400:
		message = payload.get("message") if isinstance(payload, dict) else str(payload)
		raise WhatappServiceError(message or f"Remote service returned {response.status_code}")

	return unwrap_response(payload)