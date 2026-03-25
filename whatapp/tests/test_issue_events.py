from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext.crm.doctype.lead.test_lead import make_lead
from erpnext.selling.doctype.customer.test_customer import make_customer
from erpnext.support.doctype.issue.test_issue import make_issue
from whatapp.issue_events import resolve_issue_recipient, send_issue_created_message, send_issue_status_message


class TestIssueEvents(FrappeTestCase):
	def test_issue_prefers_customer_then_lead_then_contact(self):
		customer = make_customer("Whatapp Issue Customer")
		lead = make_lead(email_id="whatapp-issue-lead@example.com")
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Issue",
				"last_name": "Contact",
				"phone_nos": [{"phone": "+966500001111", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)

		issue = make_issue(customer=customer, index=901)
		issue.lead = lead.name
		issue.contact = contact.name

		self.assertEqual(resolve_issue_recipient(issue), {"doctype": "Customer", "name": customer})

		issue.customer = ""
		self.assertEqual(resolve_issue_recipient(issue), {"doctype": "Lead", "name": lead.name})

		issue.lead = ""
		self.assertEqual(resolve_issue_recipient(issue), {"doctype": "Contact", "name": contact.name})

	def test_issue_created_sends_to_customer(self):
		customer = make_customer("Whatapp Issue Notify Customer")
		issue = make_issue(customer=customer, index=902)

		with patch("whatapp.issue_events.send_recipient_message") as mocked_send:
			send_issue_created_message(issue)

		mocked_send.assert_called_once()
		args, kwargs = mocked_send.call_args
		self.assertEqual(args[0], "Customer")
		self.assertEqual(args[1], customer)
		self.assertEqual(kwargs["event_type"], "issue_created")

	def test_issue_status_change_sends_to_lead(self):
		lead = make_lead(email_id="whatapp-issue-status@example.com")
		issue = make_issue(index=903)
		issue.customer = ""
		issue.lead = lead.name
		issue.status = "Resolved"

		with patch("whatapp.issue_events.send_recipient_message") as mocked_send:
			send_issue_status_message(issue)

		mocked_send.assert_called_once()
		args, kwargs = mocked_send.call_args
		self.assertEqual(args[0], "Lead")
		self.assertEqual(args[1], lead.name)
		self.assertEqual(kwargs["event_type"], "issue_status_resolved")