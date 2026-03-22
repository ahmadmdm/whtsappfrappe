app_name = "whatapp"
app_title = "Whatapp"
app_publisher = "Ahmad"
app_description = "Frappe UI desk for Go WhatsApp multi-device service"
app_email = "info@ideaorbit.net"
app_license = "MIT"
app_version = "0.2.0"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "whatapp",
		"logo": "/assets/whatapp/images/whatapp-logo.svg",
		"title": "Whatapp",
		"route": "/app/whatapp",
	}
]

doc_events = {
	"Notification Log": {
		"after_insert": "whatapp.notification_forwarding.on_notification_log_after_insert",
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