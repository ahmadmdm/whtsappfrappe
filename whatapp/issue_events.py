from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr, get_url_to_form

from whatapp.user_delivery import send_recipient_message


STATUS_LABELS = {
	"Open": _("مفتوحة"),
	"Replied": _("تم الرد"),
	"On Hold": _("معلقة"),
	"Resolved": _("تم الحل"),
	"Closed": _("مغلقة"),
}


def on_issue_after_insert(doc, method=None):
	schedule_issue_message("created", doc.name)


def on_issue_on_update(doc, method=None):
	if doc.is_new() or not doc.has_value_changed("status"):
		return
	schedule_issue_message("status_changed", doc.name)


def schedule_issue_message(event_name: str, docname: str):
	frappe.db.after_commit.add(lambda event_name=event_name, docname=docname: dispatch_issue_message(event_name, docname))


def dispatch_issue_message(event_name: str, docname: str):
	try:
		doc = frappe.get_doc("Issue", docname)
		if event_name == "created":
			send_issue_created_message(doc)
		elif event_name == "status_changed":
			send_issue_status_message(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Whatapp issue {event_name} notification failed")


def send_issue_created_message(doc):
	recipient = resolve_issue_recipient(doc)
	if not recipient:
		return None

	message = "\n".join(
		[
			f"تم إنشاء تذكرة دعم جديدة: {doc.subject}",
			f"رقم التذكرة: {doc.name}",
			f"الحالة: {STATUS_LABELS.get(doc.status, doc.status)}",
			get_issue_link(doc.name),
		]
	)
	return send_recipient_message(
		recipient["doctype"],
		recipient["name"],
		event_type="issue_created",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		context=build_issue_context(doc, recipient=recipient, event_name="created"),
	)


def send_issue_status_message(doc):
	recipient = resolve_issue_recipient(doc)
	if not recipient:
		return None

	message = "\n".join(
		[
			f"تم تحديث حالة تذكرة الدعم: {doc.subject}",
			f"رقم التذكرة: {doc.name}",
			f"الحالة الجديدة: {STATUS_LABELS.get(doc.status, doc.status)}",
			get_issue_link(doc.name),
		]
	)
	return send_recipient_message(
		recipient["doctype"],
		recipient["name"],
		event_type=f"issue_status_{cstr(doc.status or '').strip().lower().replace(' ', '_')}",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		context=build_issue_context(doc, recipient=recipient, event_name="status_changed"),
	)


def resolve_issue_recipient(doc) -> dict | None:
	for doctype, value in (("Customer", doc.customer), ("Lead", doc.lead), ("Contact", doc.contact)):
		name = (value or "").strip()
		if name:
			return {"doctype": doctype, "name": name}
	return None


def build_issue_context(doc, *, recipient: dict, event_name: str) -> dict:
	return {
		"issue": doc.name,
		"subject": doc.subject,
		"status": doc.status,
		"customer": doc.customer or "",
		"lead": doc.lead or "",
		"contact": doc.contact or "",
		"recipient_doctype": recipient.get("doctype") or "",
		"recipient_name": recipient.get("name") or "",
		"event_name": event_name,
	}


def get_issue_link(name: str) -> str:
	return get_url_to_form("Issue", name)
