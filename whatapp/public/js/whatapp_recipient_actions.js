(function () {
	const SUPPORTED_DOCTYPES = ["Employee", "Customer", "Supplier", "Lead", "Contact"]

	function escapeHtml(value) {
		return frappe.utils.escape_html(value || "")
	}

	function addButton(frm) {
		if (!SUPPORTED_DOCTYPES.includes(frm.doctype) || frm.is_new()) {
			return
		}

		frm.add_custom_button(__("Send WhatsApp"), () => openDialog(frm), __("Actions"))
	}

	async function openDialog(frm) {
		let recipient
		try {
			recipient = await resolveRecipient(frm)
		} catch (error) {
			showFailure(error, __("Unable to resolve a WhatsApp number for this record."))
			return
		}

		const dialog = new frappe.ui.Dialog({
			title: __("Send WhatsApp"),
			fields: [
				{
					fieldname: "recipient_info",
					fieldtype: "HTML",
				},
				{
					fieldname: "event_type",
					fieldtype: "Data",
					label: __("Event Type"),
					default: "manual_form_send",
					description: __("Saved with the WhatsApp message log."),
				},
				{
					fieldname: "message",
					fieldtype: "Small Text",
					label: __("Message"),
					reqd: 1,
					default: buildDefaultMessage(frm),
				},
			],
			primary_action_label: __("Send"),
			primary_action: async (values) => {
				try {
					await sendMessage(frm, values, recipient, dialog)
				} catch (error) {
					showFailure(error, __("WhatsApp message failed to send."))
				}
			},
		})

		renderRecipientInfo(dialog, recipient)
		dialog.show()
	}

	function renderRecipientInfo(dialog, recipient) {
		dialog.get_field("recipient_info").$wrapper.html(`
			<div style="padding:12px 14px;background:#f8fafc;border:1px solid #dbe4ee;border-radius:10px;margin-bottom:12px;">
				<div style="font-weight:600;margin-bottom:6px;">${escapeHtml(__("Resolved Recipient"))}</div>
				<div><strong>${escapeHtml(__("Phone"))}:</strong> ${escapeHtml(recipient.phone_number || "-")}</div>
				<div><strong>${escapeHtml(__("Source"))}:</strong> ${escapeHtml(recipient.source || "-")}</div>
			</div>
		`)
	}

	async function resolveRecipient(frm) {
		const response = await frappe.call({
			method: "whatapp.api.resolve_recipient_info",
			args: {
				payload: {
					recipient_doctype: frm.doctype,
					recipient_name: frm.doc.name,
				},
			},
		})
		return response.message
	}

	function showFailure(error, fallbackMessage) {
		const message =
			error?.message ||
			error?.exc_type ||
			error?.messages?.[0] ||
			fallbackMessage ||
			__("WhatsApp action failed.")
		frappe.msgprint({
			title: __("WhatsApp"),
			indicator: "orange",
			message,
		})
	}

	async function sendMessage(frm, values, recipient, dialog) {
		const response = await frappe.call({
			method: "whatapp.api.send_event_message",
			args: {
				payload: {
					event_type: values.event_type,
					message: values.message,
					recipient_doctype: frm.doctype,
					recipient_name: frm.doc.name,
					reference_doctype: frm.doctype,
					reference_name: frm.doc.name,
					context: {
						form_doctype: frm.doctype,
						form_name: frm.doc.name,
					},
				},
			},
		})

		const result = response.message || {}
		if (!result.ok) {
			throw new Error(result.error_message || __("WhatsApp message failed to send."))
		}

		dialog.hide()
		frappe.show_alert({
			message: __("WhatsApp sent to {0}", [recipient.phone_number]),
			indicator: "green",
		})
	}

	function buildDefaultMessage(frm) {
		return [
			`${frm.doctype}: ${frm.doc.name}`,
			frm.doc.employee_name || frm.doc.customer_name || frm.doc.supplier_name || frm.doc.lead_name || frm.doc.full_name || frm.doc.subject || "",
		]
			.filter(Boolean)
			.join("\n")
	}

	SUPPORTED_DOCTYPES.forEach((doctype) => {
		frappe.ui.form.on(doctype, {
			refresh(frm) {
				addButton(frm)
			},
		})
	})
})()