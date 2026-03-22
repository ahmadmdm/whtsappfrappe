from __future__ import annotations

import frappe
from frappe.model.document import Document

from whatapp.utils.service import sanitize_device_id


class WhatappUserNotificationSetting(Document):
	def validate(self):
		user = frappe.session.user
		if user == "Administrator" or "System Manager" in frappe.get_roles(user):
			sanitize_device_id(self.device_id, "Device ID Override", allow_empty=True)
			return
		sanitize_device_id(self.device_id, "Device ID Override", allow_empty=True)
		if self.user and self.user != user:
			frappe.throw("You can only manage your own Whatapp notification settings.")


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return
	if "System Manager" in frappe.get_roles(user):
		return
	return f"(`tabWhatapp User Notification Setting`.user = {frappe.db.escape(user)})"


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	if "System Manager" in frappe.get_roles(user):
		return True
	return doc.user == user