from . import __version__ as app_version


app_name = "whatapp"
app_title = "Whatapp"
app_publisher = "Ahmad"
app_description = "Frappe UI desk for Go WhatsApp multi-device service"
app_email = "info@ideaorbit.net"
app_license = "MIT"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "whatapp",
		"logo": "/assets/whatapp/images/whatapp-logo.svg",
		"title": "Whatapp",
		"route": "/app/whatapp",
	}
]

doctype_js = {
	"Employee": "public/js/whatapp_recipient_actions.js",
	"Customer": "public/js/whatapp_recipient_actions.js",
	"Supplier": "public/js/whatapp_recipient_actions.js",
	"Lead": "public/js/whatapp_recipient_actions.js",
	"Contact": "public/js/whatapp_recipient_actions.js",
}

doc_events = {
	"Notification Log": {
		"after_insert": "whatapp.notification_forwarding.on_notification_log_after_insert",
	},
	"Leave Application": {
		"after_insert": "whatapp.hrms_events.on_leave_application_after_insert",
		"on_submit": "whatapp.hrms_events.on_leave_application_on_submit",
		"on_cancel": "whatapp.hrms_events.on_leave_application_on_cancel",
	},
	"Issue": {
		"after_insert": "whatapp.issue_events.on_issue_after_insert",
		"on_update": "whatapp.issue_events.on_issue_on_update",
	}
}

permission_query_conditions = {
	"Whatapp User Notification Setting": "whatapp.whatapp.doctype.whatapp_user_notification_setting.whatapp_user_notification_setting.get_permission_query_conditions"
}

has_permission = {
	"Whatapp User Notification Setting": "whatapp.whatapp.doctype.whatapp_user_notification_setting.whatapp_user_notification_setting.has_permission"
}

after_install = "whatapp.setup.after_install"

after_migrate = ["whatapp.setup.apply_singleton_defaults"]