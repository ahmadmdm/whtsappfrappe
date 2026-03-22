import { createRouter, createMemoryHistory } from "vue-router"
import OverviewPage from "./pages/OverviewPage.vue"
import ChatsPage from "./pages/ChatsPage.vue"
import SettingsPage from "./pages/SettingsPage.vue"

export default createRouter({
	history: createMemoryHistory(),
	routes: [
		{ path: "/", name: "overview", component: OverviewPage },
		{ path: "/chats", name: "chats", component: ChatsPage },
		{ path: "/settings", name: "settings", component: SettingsPage },
	],
})