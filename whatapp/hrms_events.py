from __future__ import annotations

import frappe
from frappe.utils import cstr, formatdate, flt, get_url_to_form

from whatapp.user_delivery import send_recipient_message


def on_leave_application_after_insert(doc, method=None):
	schedule_leave_application_message("approver", doc.name)


def on_leave_application_on_submit(doc, method=None):
	schedule_leave_application_message("submitted", doc.name)


def on_leave_application_on_cancel(doc, method=None):
	schedule_leave_application_message("cancelled", doc.name)


def schedule_leave_application_message(event_name: str, docname: str):
	frappe.db.after_commit.add(lambda event_name=event_name, docname=docname: dispatch_leave_application_message(event_name, docname))


def dispatch_leave_application_message(event_name: str, docname: str):
	try:
		doc = frappe.get_doc("Leave Application", docname)
		if event_name == "approver":
			send_leave_application_approver_message(doc)
		elif event_name == "submitted":
			send_leave_application_employee_status(doc)
		elif event_name == "cancelled":
			send_leave_application_employee_cancellation(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Whatapp leave application {event_name} notification failed")


def send_leave_application_approver_message(doc):
	approver = (doc.leave_approver or "").strip()
	requester = get_employee_user(doc.employee)
	if not approver or approver == requester:
		return None
	approver_employee = get_employee_for_user(approver)
	recipient_doctype = "Employee" if approver_employee else "User"
	recipient_name = approver_employee or approver

	message = "\n".join(
		[
			f"طلب إجازة جديد من {doc.employee_name}",
			f"النوع: {doc.leave_type}",
			f"الفترة: {formatdate(doc.from_date)} إلى {formatdate(doc.to_date)}",
			f"المدة: {format_leave_days(doc.total_leave_days)} يوم",
			get_form_link(doc.doctype, doc.name),
		]
	)
	return send_recipient_message(
		recipient_doctype,
		recipient_name,
		event_type="leave_application_requested",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		context=build_leave_context(doc, recipient=recipient_name, recipient_doctype=recipient_doctype, actor_user=requester),
	)


def send_leave_application_employee_status(doc):
	if not doc.employee:
		return None

	status = cstr(doc.status or "").strip()
	if status not in {"Approved", "Rejected"}:
		return None

	status_label = "اعتماد" if status == "Approved" else "رفض"
	approver_name = frappe.db.get_value("User", doc.modified_by, "full_name") or doc.modified_by
	message = "\n".join(
		[
			f"تم {status_label} طلب الإجازة الخاص بك",
			f"النوع: {doc.leave_type}",
			f"الفترة: {formatdate(doc.from_date)} إلى {formatdate(doc.to_date)}",
			f"المدة: {format_leave_days(doc.total_leave_days)} يوم",
			f"بواسطة: {approver_name}",
			get_form_link(doc.doctype, doc.name),
		]
	)
	return send_recipient_message(
		"Employee",
		doc.employee,
		event_type=f"leave_application_{status.lower()}",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		context=build_leave_context(doc, recipient=doc.employee, recipient_doctype="Employee", actor_user=doc.modified_by),
	)


def send_leave_application_employee_cancellation(doc):
	if not doc.employee:
		return None

	message = "\n".join(
		[
			"تم إلغاء طلب الإجازة الخاص بك",
			f"النوع: {doc.leave_type}",
			f"الفترة: {formatdate(doc.from_date)} إلى {formatdate(doc.to_date)}",
			get_form_link(doc.doctype, doc.name),
		]
	)
	return send_recipient_message(
		"Employee",
		doc.employee,
		event_type="leave_application_cancelled",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		context=build_leave_context(doc, recipient=doc.employee, recipient_doctype="Employee", actor_user=doc.modified_by),
	)


def get_employee_user(employee: str | None) -> str:
	return (frappe.db.get_value("Employee", employee, "user_id") or "").strip()


def get_employee_for_user(user: str | None) -> str:
	return (frappe.db.get_value("Employee", {"user_id": user}, "name") or "").strip()


def build_leave_context(doc, *, recipient: str, recipient_doctype: str, actor_user: str | None = None) -> dict:
	return {
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"leave_type": doc.leave_type,
		"from_date": cstr(doc.from_date),
		"to_date": cstr(doc.to_date),
		"total_leave_days": doc.total_leave_days,
		"status": doc.status,
		"recipient": recipient,
		"recipient_doctype": recipient_doctype,
		"actor_user": actor_user or "",
	}


def get_form_link(doctype: str, name: str) -> str:
	return get_url_to_form(doctype, name)


def format_leave_days(value) -> str:
	amount = flt(value)
	if amount.is_integer():
		return str(int(amount))
	return cstr(amount)
