from __future__ import annotations

import frappe
from frappe.utils import cint, get_datetime, now_datetime

from whatapp.delivery import create_message_log, send_outbound_message, update_message_log
from whatapp.notification_forwarding import (
	get_user_notification_settings,
	is_self_target,
	resolve_device_id,
	update_user_setting_status,
)
from whatapp.recipient_resolver import resolve_recipient
from whatapp.utils.service import get_settings_doc


def send_user_message(
	user: str | None,
	*,
	event_type: str,
	message: str,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	context: dict | None = None,
):
	return send_recipient_message(
		"User",
		user,
		event_type=event_type,
		message=message,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		context=context,
	)


def send_recipient_message(
	recipient_doctype: str | None,
	recipient_name: str | None,
	*,
	event_type: str,
	message: str,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	context: dict | None = None,
	phone_number: str | None = None,
	recipient_user: str | None = None,
):
	if not recipient_doctype or not recipient_name:
		return None

	settings = get_settings_doc()
	if not cint(settings.enabled):
		return None

	try:
		resolved = resolve_recipient(
			recipient_doctype,
			recipient_name,
			phone_number=phone_number,
		)
	except frappe.ValidationError as exc:
		return create_message_log(
			event_type=event_type,
			status="Failed",
			phone_number=(phone_number or "unknown").strip() or "unknown",
			message=message,
			recipient_user=recipient_user,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			context=merge_context(
				context,
				{
					"recipient_doctype": recipient_doctype,
					"recipient_name": recipient_name,
					"resolve_error": str(exc),
				},
			),
		)

	resolved_user = (recipient_user or resolved.get("recipient_user") or "").strip() or None
	user_settings = get_user_notification_settings(resolved_user) if resolved_user else None
	if user_settings and not cint(user_settings.enabled):
		return create_message_log(
			event_type=event_type,
			status="Skipped",
			phone_number=resolved["phone_number"],
			message=message,
			recipient_user=resolved_user,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			context=build_recipient_context(context, resolved),
		)

	if user_settings and user_settings.mute_until and get_datetime(user_settings.mute_until) > now_datetime():
		return create_message_log(
			event_type=event_type,
			status="Skipped",
			phone_number=resolved["phone_number"],
			message=message,
			recipient_user=resolved_user,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			context=build_recipient_context(context, resolved),
		)

	device_id = resolve_device_id(settings, user_settings)
	if is_self_target(device_id, resolved["phone_number"]):
		log = create_message_log(
			event_type=event_type,
			status="Skipped",
			phone_number=resolved["phone_number"],
			message=message,
			device_id=device_id,
			recipient_user=resolved_user,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			context=build_recipient_context(context, resolved),
		)
		update_message_log(
			log,
			status="Skipped",
			error_message="Target WhatsApp number matches the logged-in sending account; self-notifications will not appear as a separate incoming alert.",
		)
		update_user_setting_status(
			user_settings,
			error="Target WhatsApp number matches the logged-in sending account; self-notifications will not appear as a separate incoming alert.",
		)
		return log

	log = send_outbound_message(
		event_type=event_type,
		phone_number=resolved["phone_number"],
		message=message,
		device_id=device_id,
		recipient_user=resolved_user,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		context=build_recipient_context(context, resolved),
	)

	if log.status == "Sent":
		update_user_setting_status(user_settings, delivered=True)
	elif log.status == "Failed":
		update_user_setting_status(user_settings, error=log.error_message)
	elif log.status == "Skipped":
		update_user_setting_status(user_settings, error=log.error_message or "Skipped")

	return log


def build_recipient_context(context: dict | None, resolved: dict) -> dict:
	return merge_context(
		context,
		{
			"recipient_doctype": resolved.get("recipient_doctype") or "",
			"recipient_name": resolved.get("recipient_name") or "",
			"phone_source": resolved.get("source") or "",
		},
	)


def merge_context(context: dict | None, extra: dict) -> dict:
	merged = dict(context or {})
	merged.update(extra)
	return merged
