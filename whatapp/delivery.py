from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from whatapp.utils.service import WhatappServiceError, get_settings_doc, request_service, sanitize_device_id


def send_outbound_message(
	*,
	event_type: str,
	phone_number: str,
	message: str,
	device_id: str | None = None,
	recipient_user: str | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	context: dict[str, Any] | None = None,
) -> frappe.model.document.Document:
	phone_number = (phone_number or "").strip()
	message = (message or "").strip()
	event_type = (event_type or "system").strip()
	selected_device_id = sanitize_device_id(device_id, "Device ID", allow_empty=True) or ""

	if not phone_number:
		frappe.throw("phone_number is required")
	if not message:
		frappe.throw("message is required")

	log = create_message_log(
		event_type=event_type,
		status="Queued",
		phone_number=phone_number,
		message=message,
		device_id=selected_device_id,
		recipient_user=recipient_user,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		context=context,
	)

	settings = get_settings_doc()
	if not settings.enabled:
		return update_message_log(log, status="Skipped", error_message="Whatapp is disabled in settings")

	try:
		request_service(
			"POST",
			"/send/message",
			json_data={"phone": phone_number, "message": message},
			device_id=selected_device_id or None,
		)
	except frappe.ValidationError as exc:
		return update_message_log(log, status="Failed", error_message=str(exc))
	except WhatappServiceError as exc:
		return update_message_log(log, status="Failed", error_message=str(exc))

	return update_message_log(log, status="Sent", sent_on=now_datetime(), error_message="")


def create_message_log(
	*,
	event_type: str,
	status: str,
	phone_number: str,
	message: str,
	device_id: str | None = None,
	recipient_user: str | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	context: dict[str, Any] | None = None,
) -> frappe.model.document.Document:
	log = frappe.get_doc(
		{
			"doctype": "Whatapp Message Log",
			"direction": "Outbound",
			"status": status,
			"event_type": (event_type or "system").strip() or "system",
			"recipient_user": (recipient_user or "").strip(),
			"phone_number": (phone_number or "").strip(),
			"device_id": (device_id or "").strip(),
			"message": message,
			"reference_doctype": (reference_doctype or "").strip(),
			"reference_name": (reference_name or "").strip(),
			"context_json": format_context_json(context),
		}
	)
	log.insert(ignore_permissions=True)
	return log


def update_message_log(
	log,
	*,
	status: str,
	error_message: str | None = None,
	sent_on=None,
):
	updates = {"status": status}
	if sent_on is not None:
		updates["sent_on"] = sent_on
	if error_message is not None:
		updates["error_message"] = (error_message or "")[:140]

	for fieldname, value in updates.items():
		log.db_set(fieldname, value, update_modified=False)
		setattr(log, fieldname, value)

	return log


def format_context_json(context: dict[str, Any] | None) -> str:
	if not context:
		return ""
	try:
		return json.dumps(context, ensure_ascii=False, indent=2, default=str)
	except Exception:
		return json.dumps({"raw": str(context)}, ensure_ascii=False, indent=2)
