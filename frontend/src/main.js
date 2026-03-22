import "./index.css"

import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import { Toasts, setConfig, frappeRequest, resourcesPlugin } from "frappe-ui"

function mount(target) {
	const el = typeof target === "string" ? document.querySelector(target) : target
	if (!el) {
		throw new Error("Whatapp: mount target not found")
	}

	setConfig("resourceFetcher", frappeRequest)

	const app = createApp(App)
	app.use(router)
	app.use(resourcesPlugin)
	app.component("Toasts", Toasts)
	app.mount(el)
	return app
}

window.WhatappDesk = { mount }

export { mount }