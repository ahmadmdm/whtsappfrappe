from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext.buying.doctype.supplier.test_supplier import create_supplier
from erpnext.crm.doctype.lead.test_lead import make_lead
from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.selling.doctype.customer.test_customer import make_customer
from whatapp.recipient_resolver import resolve_recipient


class TestRecipientResolver(FrappeTestCase):
	def test_employee_uses_cell_number(self):
		employee = make_employee("whatapp_employee@example.com")
		frappe.db.set_value("Employee", employee, "cell_number", "+966500000111")

		resolved = resolve_recipient("Employee", employee)

		self.assertEqual(resolved["phone_number"], "+966500000111")
		self.assertEqual(resolved["source"], "Employee.cell_number")

	def test_customer_uses_mobile_no(self):
		customer = make_customer("Whatapp Resolver Customer")
		frappe.db.set_value("Customer", customer, "mobile_no", "+966500000222")

		resolved = resolve_recipient("Customer", customer)

		self.assertEqual(resolved["phone_number"], "+966500000222")
		self.assertEqual(resolved["source"], "Customer.mobile_no")

	def test_supplier_falls_back_to_primary_contact_mobile(self):
		supplier = create_supplier(supplier_name="Whatapp Resolver Supplier")
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Supplier",
				"last_name": "Contact",
				"is_primary_contact": 1,
				"phone_nos": [{"phone": "+966500000333", "is_primary_mobile_no": 1}],
				"links": [{"link_doctype": "Supplier", "link_name": supplier.name}],
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Supplier", supplier.name, "supplier_primary_contact", contact.name)

		resolved = resolve_recipient("Supplier", supplier.name)

		self.assertEqual(resolved["phone_number"], "+966500000333")
		self.assertEqual(resolved["source"], f"Contact.mobile_no:{contact.name}")

	def test_lead_prefers_whatsapp_number(self):
		lead = make_lead(email_id="whatapp-resolver@example.com")
		frappe.db.set_value("Lead", lead.name, "mobile_no", "+966500000444")
		frappe.db.set_value("Lead", lead.name, "whatsapp_no", "+966500000555")

		resolved = resolve_recipient("Lead", lead.name)

		self.assertEqual(resolved["phone_number"], "+966500000555")
		self.assertEqual(resolved["source"], "Lead.whatsapp_no")