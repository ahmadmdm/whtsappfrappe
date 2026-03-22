from __future__ import annotations

import hashlib
import hmac
import json

import frappe
from frappe import _
from frappe.utils import cint

from whatapp.local_service import sync_local_service_config
from whatapp.utils.service import (
	WhatappServiceError,
	get_settings_doc,
	request_service,
	sanitize_device_id,
)


def _parse_payload(payload):
	if not payload:
		return {}
	if isinstance(payload, dict):
		return payload
	return frappe.parse_json(payload)


def _public_settings(doc):
	return {
		"service_url": doc.service_url or "",
		"basic_auth_username": doc.basic_auth_username or "",
		"basic_auth_password": "",
		"default_device_id": doc.default_device_id or "",
		"notification_forwarding_enabled": doc.notification_forwarding_enabled,
		"notification_default_device_id": doc.notification_default_device_id or "",
		"notification_allowed_types": doc.notification_allowed_types or "",
		"notification_skip_own": doc.notification_skip_own,
		"notification_include_link": doc.notification_include_link,
		"notification_include_content": doc.notification_include_content,
		"notification_include_sender": doc.notification_include_sender,
		"notification_max_length": doc.notification_max_length or 1000,
		"notification_message_template": doc.notification_message_template or "",
		"webhook_secret": "",
		"webhook_events": doc.webhook_events or "",
		"request_timeout": doc.request_timeout or 45,
		"enabled": doc.enabled,
		"notes": doc.notes or "",
	}


@frappe.whitelist()
def get_bootstrap():
	doc = get_settings_doc()
	result = {
		"settings": {
			"base_url": doc.service_url or "",
			"default_device_id": doc.default_device_id or "",
			"enabled": doc.enabled,
		},
		"default_device_id": doc.default_device_id or "",
		"webhook_url": f"{frappe.utils.get_url()}/api/method/whatapp.api.receive_webhook",
		"devices": [],
	}

	if not doc.service_url:
		return result

	try:
		result["devices"] = list_devices(raw=True)
		if not result["default_device_id"] and result["devices"]:
			result["default_device_id"] = result["devices"][0].get("id")
	except WhatappServiceError as exc:
		result["service_error"] = str(exc)

	return result


@frappe.whitelist()
def get_settings():
	return _public_settings(get_settings_doc())


@frappe.whitelist()
def save_settings(payload=None):
	data = _parse_payload(payload)
	doc = get_settings_doc()
	device_labels = {
		"default_device_id": _("Default Device ID"),
		"notification_default_device_id": _("Notification Device ID"),
	}
	fields = [
		"service_url",
		"basic_auth_username",
		"default_device_id",
		"notification_forwarding_enabled",
		"notification_default_device_id",
		"notification_allowed_types",
		"notification_skip_own",
		"notification_include_link",
		"notification_include_content",
		"notification_include_sender",
		"notification_max_length",
		"notification_message_template",
		"webhook_events",
		"request_timeout",
		"enabled",
		"notes",
	]
	for fieldname in fields:
		if fieldname in data:
			value = data.get(fieldname)
			if fieldname in device_labels:
				value = sanitize_device_id(value, device_labels[fieldname], allow_empty=True) or ""
			setattr(doc, fieldname, value)

	if data.get("basic_auth_password"):
		doc.basic_auth_password = data.get("basic_auth_password")
	if data.get("webhook_secret"):
		doc.webhook_secret = data.get("webhook_secret")

	doc.save(ignore_permissions=True)
	sync_local_service_config(doc)
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist()
def list_notification_users(search=None):
	frappe.only_for("System Manager")
	filters = {
		"enabled": 1,
		"user_type": "System User",
		"name": ["not in", ["Guest"]],
	}
	or_filters = None
	if search:
		term = f"%{search.strip()}%"
		or_filters = [["User", "name", "like", term], ["User", "full_name", "like", term]]

	users = frappe.get_all(
		"User",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "full_name", "whatapp_whatsapp_number", "mobile_no", "phone", "enabled"],
		order_by="full_name asc, name asc",
		limit_page_length=200,
	)
	settings_rows = frappe.get_all(
		"Whatapp User Notification Setting",
		fields=[
			"name",
			"user",
			"enabled",
			"phone_number",
			"device_id",
			"allowed_notification_types",
			"last_delivery_on",
			"last_error",
		],
	)
	settings_by_user = {row.user: row for row in settings_rows}
	results = []
	for user in users:
		setting = settings_by_user.get(user.name)
		whatsapp_number = (user.whatapp_whatsapp_number or "").strip()
		system_phone = whatsapp_number or (user.mobile_no or "").strip() or (user.phone or "").strip()
		results.append(
			{
				"user": user.name,
				"full_name": user.full_name or user.name,
				"system_phone": system_phone,
				"whatsapp_number": whatsapp_number,
				"mobile_no": user.mobile_no or "",
				"phone": user.phone or "",
				"setting_name": setting.name if setting else "",
				"enabled": cint(setting.enabled) if setting else 0,
				"phone_number": (setting.phone_number or "").strip() if setting else "",
				"device_id": (setting.device_id or "").strip() if setting else "",
				"allowed_notification_types": (setting.allowed_notification_types or "").strip() if setting else "",
				"last_delivery_on": setting.last_delivery_on if setting else None,
				"last_error": setting.last_error if setting else "",
				"has_system_phone": 1 if system_phone else 0,
			}
		)
	return {"data": results}


@frappe.whitelist()
def save_notification_users(payload=None):
	frappe.only_for("System Manager")
	rows = _parse_payload(payload)
	if not isinstance(rows, list):
		frappe.throw("payload must be a list")

	updated = []
	for row in rows:
		user = (row.get("user") or "").strip()
		if not user:
			continue
		if not frappe.db.exists("User", user):
			frappe.throw(_("User {0} does not exist.").format(user))

		name = frappe.db.exists("Whatapp User Notification Setting", user)
		if name:
			doc = frappe.get_doc("Whatapp User Notification Setting", name)
		else:
			doc = frappe.new_doc("Whatapp User Notification Setting")
			doc.user = user

		doc.enabled = cint(row.get("enabled"))
		doc.phone_number = (row.get("phone_number") or "").strip()
		doc.device_id = sanitize_device_id(row.get("device_id"), _("Device ID Override"), allow_empty=True) or ""
		doc.allowed_notification_types = (row.get("allowed_notification_types") or "").strip()
		doc.save(ignore_permissions=True)
		updated.append(doc.user)

	frappe.db.commit()
	return {"ok": True, "updated": updated}


@frappe.whitelist()
def list_devices(raw=False):
	result = request_service("GET", "/devices")
	return result if raw else {"data": result}


@frappe.whitelist()
def create_device(device_id=None):
	device = request_service(
		"POST",
		"/devices",
		json_data={"device_id": sanitize_device_id(device_id, _("Device ID"), allow_empty=True) or ""},
	)
	return {"message": "Device created", "device": device}


@frappe.whitelist()
def request_login_qr(device_id=None):
	result = request_service("GET", "/app/login", device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False))
	return {
		"message": "QR generated",
		"device_id": result.get("device_id"),
		"qr_link": result.get("qr_link"),
		"qr_duration": result.get("qr_duration"),
	}


@frappe.whitelist()
def request_pair_code(device_id=None, phone=None):
	result = request_service(
		"GET",
		"/app/login-with-code",
		params={"phone": phone},
		device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False),
	)
	return {
		"message": "Pair code generated",
		"device_id": result.get("device_id"),
		"pair_code": result.get("pair_code"),
	}


@frappe.whitelist()
def request_logout(device_id=None):
	result = request_service("GET", "/app/logout", device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False))
	return {"message": "Logout requested", **(result or {})}


@frappe.whitelist()
def request_reconnect(device_id=None):
	result = request_service("GET", "/app/reconnect", device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False))
	return {"message": "Reconnect requested", **(result or {})}


@frappe.whitelist()
def get_device_status(device_id=None):
	if device_id:
		result = request_service("GET", f"/devices/{device_id}/status")
	else:
		result = request_service("GET", "/app/status")
	return result


@frappe.whitelist()
def list_chats(device_id=None, search=None, limit=40, offset=0, archived=None):
	params = {
		"search": search or "",
		"limit": int(limit or 40),
		"offset": int(offset or 0),
	}
	if archived in ("0", "1", 0, 1, True, False):
		params["archived"] = int(bool(int(archived))) if isinstance(archived, str) else int(bool(archived))
	return request_service(
		"GET",
		"/chats",
		params=params,
		device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False),
	)


@frappe.whitelist()
def get_chat_messages(device_id=None, chat_jid=None, limit=60, offset=0):
	if not chat_jid:
		frappe.throw("chat_jid is required")
	return request_service(
		"GET",
		f"/chat/{chat_jid}/messages",
		params={"limit": int(limit or 60), "offset": int(offset or 0)},
		device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False),
	)


@frappe.whitelist()
def send_text_message(device_id=None, phone=None, message=None, reply_message_id=None):
	if not phone or not message:
		frappe.throw("phone and message are required")
	payload = {"phone": phone, "message": message}
	if reply_message_id:
		payload["reply_message_id"] = reply_message_id
	return request_service(
		"POST",
		"/send/message",
		json_data=payload,
		device_id=sanitize_device_id(device_id, _("Device ID"), allow_empty=False),
	)


@frappe.whitelist(allow_guest=True)
def receive_webhook():
	data = frappe.request.get_data() or b""
	signature = frappe.get_request_header("X-Hub-Signature-256") or ""
	doc = get_settings_doc()
	secret = doc.get_password("webhook_secret") or ""

	is_valid = True
	if secret:
		expected = "sha256=" + hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
		is_valid = hmac.compare_digest(expected, signature)

	if secret and not is_valid:
		frappe.local.response.http_status_code = 403
		return {"ok": False, "message": "Invalid webhook signature"}

	payload = json.loads(data.decode("utf-8") or "{}") if data else {}
	if not isinstance(payload, dict):
		payload = {"raw": payload}
	log = frappe.get_doc(
		{
			"doctype": "Whatapp Webhook Log",
			"event": payload.get("event") or "unknown",
			"device_id": payload.get("device_id") or "",
			"signature_valid": 1 if is_valid else 0,
			"payload_json": json.dumps(payload, ensure_ascii=False, indent=2),
		}
	)
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True}


def ensure_integrations_workspace_link():
	workspace = frappe.get_doc("Workspace", "Integrations")
	links = list(workspace.links or [])

	has_card = any(link.label == "Whatapp" and link.type == "Card Break" for link in links)
	has_link = any(
		link.label == "Whatapp" and link.type == "Link" and link.link_type == "Page" and link.link_to == "whatapp"
		for link in links
	)

	if not has_card:
		workspace.append(
			"links",
			{
				"label": "Whatapp",
				"type": "Card Break",
				"link_count": 1,
				"onboard": 0,
			},
		)

	if not has_link:
		workspace.append(
			"links",
			{
				"label": "Whatapp",
				"type": "Link",
				"link_type": "Page",
				"link_to": "whatapp",
				"onboard": 1,
			},
		)

	content = json.loads(workspace.content or "[]")
	has_content_card = any(
		block.get("type") == "card" and (block.get("data") or {}).get("card_name") == "Whatapp"
		for block in content
	)
	if not has_content_card:
		content.append({"id": "whatappCard01", "type": "card", "data": {"card_name": "Whatapp", "col": 4}})
		workspace.content = json.dumps(content, separators=(",", ":"))

	workspace.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True}