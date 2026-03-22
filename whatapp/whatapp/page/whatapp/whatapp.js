frappe.pages["whatapp"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Whatapp",
		single_column: true,
	})

	frappe.breadcrumbs.add("Whatapp")
	$(wrapper).find(".page-content").css({ padding: "0", margin: "0" })
	page.main.css({ padding: "0", margin: "0", "max-width": "100%" })

	const container = document.createElement("div")
	container.id = "whatapp-root"
	page.main.append(container)

	loadWhatappDesk()
		.then(() => {
			window.WhatappDesk.mount(container)
		})
		.catch((error) => {
			container.innerHTML = `
				<div style="display:flex;min-height:60vh;align-items:center;justify-content:center;flex-direction:column;gap:12px;font-family:sans-serif;">
					<div style="font-size:1.2rem;font-weight:700;color:#bb5142;">Whatapp failed to load</div>
					<div style="color:#76695a;">${error.message}</div>
				</div>
			`
		})
}

let whatappPromise = null

function loadWhatappDesk() {
	if (window.WhatappDesk) return Promise.resolve()
	if (whatappPromise) return whatappPromise

	const version = "20260322g"
	whatappPromise = Promise.all([
		injectStylesheet(`/assets/whatapp/dist/whatapp.bundle.css?v=${version}`),
		injectScript(`/assets/whatapp/dist/whatapp.bundle.js?v=${version}`),
	]).then(
		() =>
			new Promise((resolve) => {
				const poll = () => (window.WhatappDesk ? resolve() : setTimeout(poll, 50))
				poll()
			})
	)

	return whatappPromise
}

function injectScript(src) {
	return new Promise((resolve, reject) => {
		if (document.querySelector(`script[src="${src}"]`)) return resolve()
		const base = src.split("?")[0]
		document.querySelectorAll(`script[src^="${base}"]`).forEach((el) => el.remove())
		const script = document.createElement("script")
		script.src = src
		script.onload = resolve
		script.onerror = () => reject(new Error(`Script load failed: ${src}`))
		document.head.appendChild(script)
	})
}

function injectStylesheet(href) {
	return new Promise((resolve) => {
		if (document.querySelector(`link[href="${href}"]`)) return resolve()
		const base = href.split("?")[0]
		document.querySelectorAll(`link[href^="${base}"]`).forEach((el) => el.remove())
		const link = document.createElement("link")
		link.rel = "stylesheet"
		link.href = href
		link.onload = resolve
		link.onerror = resolve
		document.head.appendChild(link)
	})
}