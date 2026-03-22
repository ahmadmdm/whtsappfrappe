import { toast } from "frappe-ui"

export function notifySuccess(text) {
	toast({
		title: "Success",
		text,
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

export function notifyError(text) {
	toast({
		title: "Error",
		text,
		icon: "alert-circle",
		position: "bottom-center",
		iconClasses: "text-red-500",
	})
}