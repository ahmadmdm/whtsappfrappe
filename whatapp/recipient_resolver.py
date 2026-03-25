from __future__ import annotations

from typing import Any

import frappe
from frappe.contacts.doctype.contact.contact import get_default_contact


PARTY_FIELD_PRIORITIES = {
	"User": ("whatapp_whatsapp_number", "mobile_no", "phone"),
	"Employee": ("cell_number", "personal_email", "company_email"),
	"Lead": ("whatsapp_no", "mobile_no", "phone"),
	"Customer": ("mobile_no",),
	"Supplier": ("mobile_no",),
	"Contact": ("mobile_no", "phone"),
}


def resolve_recipient(
	recipient_doctype: str | None,
	recipient_name: str | None,
	*,
	phone_number: str | None = None,
) -> dict[str, Any]:
	recipient_doctype = (recipient_doctype or "").strip()
	recipient_name = (recipient_name or "").strip()
	manual_phone = (phone_number or "").strip()

	if manual_phone:
		return {
			"recipient_doctype": recipient_doctype,
			"recipient_name": recipient_name,
			"phone_number": manual_phone,
			"recipient_user": resolve_related_user(recipient_doctype, recipient_name),
			"source": "manual",
		}

	if not recipient_doctype or not recipient_name:
		frappe.throw("recipient_doctype and recipient_name are required when phone is not provided")

	if not frappe.db.exists(recipient_doctype, recipient_name):
		frappe.throw(f"{recipient_doctype} {recipient_name} does not exist")

	phone = resolve_phone_number_for_party(recipient_doctype, recipient_name)
	if not phone:
		frappe.throw(f"No mobile or WhatsApp number found for {recipient_doctype} {recipient_name}")

	return {
		"recipient_doctype": recipient_doctype,
		"recipient_name": recipient_name,
		"phone_number": phone,
		"recipient_user": resolve_related_user(recipient_doctype, recipient_name),
		"source": resolve_phone_source(recipient_doctype, recipient_name, phone),
	}


def resolve_phone_number_for_party(doctype: str, name: str) -> str | None:
	fields = PARTY_FIELD_PRIORITIES.get(doctype, ())
	for fieldname in fields:
		value = get_party_field_value(doctype, name, fieldname)
		if value and is_phone_like_field(doctype, fieldname):
			return value

	if doctype in {"Employee", "Customer", "Supplier", "Lead"}:
		contact_phone = get_linked_contact_phone(doctype, name)
		if contact_phone:
			return contact_phone

	if doctype == "Contact":
		return get_party_field_value("Contact", name, "mobile_no") or get_party_field_value("Contact", name, "phone")

	return None


def resolve_phone_source(doctype: str, name: str, phone: str) -> str:
	fields = PARTY_FIELD_PRIORITIES.get(doctype, ())
	for fieldname in fields:
		value = get_party_field_value(doctype, name, fieldname)
		if value == phone and is_phone_like_field(doctype, fieldname):
			return f"{doctype}.{fieldname}"

	if doctype in {"Employee", "Customer", "Supplier", "Lead"}:
		contact_name = get_default_contact_name(doctype, name)
		if contact_name:
			return f"Contact.mobile_no:{contact_name}"

	return "unknown"


def resolve_related_user(doctype: str | None, name: str | None) -> str | None:
	if not doctype or not name:
		return None
	if doctype == "User":
		return name
	if doctype == "Employee":
		return (frappe.db.get_value("Employee", name, "user_id") or "").strip() or None
	if doctype == "Contact":
		return (frappe.db.get_value("Contact", name, "user") or "").strip() or None
	return None


def get_party_field_value(doctype: str, name: str, fieldname: str) -> str:
	if not frappe.get_meta(doctype).has_field(fieldname):
		return ""
	value = frappe.db.get_value(doctype, name, fieldname)
	return (value or "").strip()


def is_phone_like_field(doctype: str, fieldname: str) -> bool:
	return fieldname in {"whatapp_whatsapp_number", "cell_number", "whatsapp_no", "mobile_no", "phone"}


def get_linked_contact_phone(doctype: str, name: str) -> str | None:
	contact_name = get_default_contact_name(doctype, name)
	if not contact_name:
		return None
	for fieldname in ("mobile_no", "phone"):
		value = get_party_field_value("Contact", contact_name, fieldname)
		if value:
			return value
	return None


def get_default_contact_name(doctype: str, name: str) -> str | None:
	if doctype == "Customer":
		primary_contact = get_party_field_value("Customer", name, "customer_primary_contact")
		if primary_contact:
			return primary_contact
	if doctype == "Supplier":
		primary_contact = get_party_field_value("Supplier", name, "supplier_primary_contact")
		if primary_contact:
			return primary_contact
	return get_default_contact(doctype, name)
