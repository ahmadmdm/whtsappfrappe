function normalizeError(error) {
	const serverMessage =
		error?.messages?.[0] ||
		error?.message ||
		error?._server_messages

	if (typeof serverMessage === "string") {
		try {
			const parsed = JSON.parse(serverMessage)
			if (Array.isArray(parsed) && parsed.length) {
				return JSON.parse(parsed[0]).message || "Request failed"
			}
		} catch {
			return serverMessage
		}
	}

	return "Request failed"
}

export function call(method, args = {}, type = "POST") {
	return new Promise((resolve, reject) => {
		window.frappe.call({
			method,
			args,
			type,
			callback(response) {
				resolve(response.message)
			},
			error(error) {
				reject(new Error(normalizeError(error)))
			},
		})
	})
}