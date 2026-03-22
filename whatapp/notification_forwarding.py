from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime, now_datetime, strip_html

from whatapp.utils.service import WhatappServiceError, get_settings_doc, request_service


DEFAULT_TEMPLATE = """{{ subject }}{% if content %}\n\n{{ content }}{% endif %}{% if from_user_fullname %}\n\nFrom: {{ from_user_fullname }}{% endif %}{% if link %}\n\n{{ link }}{% endif %}"""


def on_notification_log_after_insert(doc, method=None):
	try:
		forward_notification(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Whatapp notification forwarding failed")


def forward_notification(doc):
	settings = get_settings_doc()
	if not cint(settings.enabled) or not cint(settings.notification_forwarding_enabled):
		return

	if not doc.for_user or doc.for_user == "Guest":
		return

	user_profile = get_user_profile(doc.for_user)
	if not user_profile:
		return

	user_settings = get_user_notification_settings(doc.for_user)
	if user_settings and not cint(user_settings.enabled):
		return

	if cint(settings.notification_skip_own) and doc.from_user and doc.from_user == doc.for_user:
		return

	if user_settings and user_settings.mute_until and get_datetime(user_settings.mute_until) > now_datetime():
		return

	if not is_allowed_notification_type(doc.type, settings.notification_allowed_types, user_settings):
		return

	phone_number = resolve_phone_number(user_profile, user_settings)
	if not phone_number:
		update_user_setting_status(user_settings, error="Missing mobile number or phone on the target user")
		return

	message = build_message(doc, settings, user_profile)
	if not message:
		return

	device_id = resolve_device_id(settings, user_settings)
	if is_self_target(device_id, phone_number):
		update_user_setting_status(
			user_settings,
			error="Target WhatsApp number matches the logged-in sending account; self-notifications will not appear as a separate incoming alert.",
		)
		return

	try:
		request_service(
			"POST",
			"/send/message",
			json_data={"phone": phone_number, "message": message},
			device_id=device_id,
		)
	except WhatappServiceError as exc:
		update_user_setting_status(user_settings, error=str(exc))
		raise

	update_user_setting_status(user_settings, delivered=True)


def get_user_profile(user: str) -> dict[str, Any] | None:
	profile = frappe.db.get_value(
		"User",
		user,
		["name", "enabled", "full_name", "whatapp_whatsapp_number", "mobile_no", "phone"],
		as_dict=True,
	)
	if not profile or not cint(profile.enabled):
		return None
	return profile


def get_user_notification_settings(user: str):
	if not frappe.db.exists("DocType", "Whatapp User Notification Setting"):
		return None
	name = frappe.db.exists("Whatapp User Notification Setting", user)
	if not name:
		return None
	return frappe.get_doc("Whatapp User Notification Setting", name)


def resolve_phone_number(user_profile: dict[str, Any], user_settings) -> str | None:
	if user_settings and (user_settings.phone_number or "").strip():
		return user_settings.phone_number.strip()
	for fieldname in ("whatapp_whatsapp_number", "mobile_no", "phone"):
		value = (user_profile.get(fieldname) or "").strip()
		if value:
			return value
	return None


def resolve_device_id(settings, user_settings) -> str | None:
	for value in (
		getattr(user_settings, "device_id", None) if user_settings else None,
		settings.notification_default_device_id,
		settings.default_device_id,
	):
		candidate = (value or "").strip()
		if candidate:
			return candidate
	return None


def is_self_target(device_id: str | None, phone_number: str | None) -> bool:
	if not device_id or not phone_number:
		return False

	device_jid = get_device_jid(device_id)
	if not device_jid:
		return False

	return normalize_whatsapp_id(device_jid) == normalize_whatsapp_id(phone_number)


def get_device_jid(device_id: str) -> str | None:
	try:
		devices = request_service("GET", "/devices") or []
	except WhatappServiceError:
		return None

	for device in devices:
		if (device or {}).get("id") == device_id:
			return (device.get("jid") or "").strip() or None
	return None


def normalize_whatsapp_id(value: str) -> str:
	cleaned = "".join(ch for ch in (value or "") if ch.isdigit())
	if cleaned.startswith("00"):
		cleaned = cleaned[2:]
	return cleaned


def is_allowed_notification_type(notification_type: str | None, allowed_types: str | None, user_settings) -> bool:
	requested_type = (notification_type or "").strip().lower()
	global_types = parse_types(allowed_types)
	if global_types and requested_type not in global_types:
		return False

	user_types = parse_types(getattr(user_settings, "allowed_notification_types", "") if user_settings else "")
	if user_types and requested_type not in user_types:
		return False

	return True


def parse_types(value: str | None) -> set[str]:
	return {(item or "").strip().lower() for item in (value or "").split(",") if (item or "").strip()}


def build_message(doc, settings, user_profile: dict[str, Any]) -> str:
	content = strip_html(doc.email_content or "").strip() if cint(settings.notification_include_content) else ""
	link = get_notification_link(doc) if cint(settings.notification_include_link) else ""
	from_user_fullname = ""
	if cint(settings.notification_include_sender) and doc.from_user:
		from_user_fullname = frappe.db.get_value("User", doc.from_user, "full_name") or doc.from_user

	context = {
		"subject": strip_html(doc.subject or "").strip(),
		"content": content,
		"type": doc.type or "",
		"link": link,
		"user": user_profile.get("full_name") or user_profile.get("name") or "",
		"from_user": doc.from_user or "",
		"from_user_fullname": from_user_fullname,
		"document_type": doc.document_type or "",
		"document_name": doc.document_name or "",
	}

	template = (settings.notification_message_template or "").strip() or DEFAULT_TEMPLATE
	try:
		message = frappe.render_template(template, context)
	except Exception:
		message = frappe.render_template(DEFAULT_TEMPLATE, context)

	message = compact_message(message)
	max_length = max(cint(settings.notification_max_length or 1000), 120)
	if len(message) > max_length:
		message = message[: max_length - 3].rstrip() + "..."
	return message


def compact_message(message: str) -> str:
	lines = [line.rstrip() for line in (message or "").splitlines()]
	compacted = []
	blank_pending = False
	for line in lines:
		if line.strip():
			if blank_pending and compacted:
				compacted.append("")
			compacted.append(line.strip())
			blank_pending = False
		else:
			blank_pending = True
	return "\n".join(compacted).strip()


def get_notification_link(doc) -> str:
	if doc.link:
		link = doc.link.strip()
		if link.startswith("http://") or link.startswith("https://"):
			return link
		return f"{frappe.utils.get_url()}{link if link.startswith('/') else '/' + link}"

	if doc.document_type and doc.document_name:
		from frappe.utils import get_url_to_form

		return get_url_to_form(doc.document_type, doc.document_name)

	return ""


def update_user_setting_status(user_settings, delivered: bool = False, error: str | None = None):
	if not user_settings:
		return

	updates = {}
	if delivered:
		updates["last_delivery_on"] = now_datetime()
		updates["last_error"] = ""
	elif error is not None:
		updates["last_error"] = error[:140]

	if updates:
		for fieldname, value in updates.items():
			user_settings.db_set(fieldname, value, update_modified=False)