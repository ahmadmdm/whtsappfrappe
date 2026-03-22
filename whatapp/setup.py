from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from whatapp.local_service import DEFAULT_SERVICE_URL, ensure_local_service_ready, sync_local_service_config


SINGLETON_DEFAULTS = {
	"service_url": DEFAULT_SERVICE_URL,
	"notification_forwarding_enabled": 0,
	"notification_skip_own": 1,
	"notification_include_link": 1,
	"notification_include_content": 0,
	"notification_include_sender": 1,
	"notification_max_length": 1000,
}

USER_CUSTOM_FIELDS = {
	"User": [
		{
			"fieldname": "whatapp_whatsapp_number",
			"fieldtype": "Data",
			"label": "WhatsApp Number",
			"insert_after": "mobile_no",
			"options": "Phone",
			"description": "Preferred WhatsApp number used by Whatapp notification delivery.",
		},
	]
}


def ensure_user_custom_fields():
	create_custom_fields(USER_CUSTOM_FIELDS, ignore_validate=True, update=True)


def bootstrap_local_service():
	try:
		ensure_local_service_ready()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Whatapp local service bootstrap failed")


def apply_singleton_defaults():
	ensure_user_custom_fields()

	if not frappe.db.exists("DocType", "Whatapp Settings"):
		return

	doc = frappe.get_single("Whatapp Settings")
	first_run_notification_setup = is_first_run_notification_setup(doc)
	changed = False
	for fieldname, value in SINGLETON_DEFAULTS.items():
		current = frappe.db.get_single_value("Whatapp Settings", fieldname)
		if current is None or (first_run_notification_setup and fieldname in {"notification_skip_own", "notification_include_link", "notification_include_sender"}):
			setattr(doc, fieldname, value)
			changed = True

	if changed:
		doc.save(ignore_permissions=True)
		frappe.db.commit()

	sync_local_service_config(doc)
	bootstrap_local_service()


def after_install():
	apply_singleton_defaults()


def is_first_run_notification_setup(doc) -> bool:
	return not any(
		[
			(doc.notification_forwarding_enabled or 0),
			(doc.notification_default_device_id or "").strip(),
			(doc.notification_allowed_types or "").strip(),
			(doc.notification_message_template or "").strip(),
			(doc.notification_include_content or 0),
		]
	)