<script setup>
import { computed } from "vue"
import { RouterLink, RouterView, useRoute } from "vue-router"
import { Badge, FeatherIcon } from "frappe-ui"
import { useLocale } from "@/lib/i18n"

const route = useRoute()
const { dir, t } = useLocale()

const navItems = [
	{ name: "overview", label: t("navControl"), to: "/", icon: "grid" },
	{ name: "chats", label: t("navChats"), to: "/chats", icon: "message-circle" },
	{ name: "settings", label: t("navSettings"), to: "/settings", icon: "settings" },
]

const currentUser = computed(
	() => window.frappe?.session?.user_fullname || window.frappe?.session?.user || "Administrator"
)
</script>

<template>
	<div class="wa-shell" :dir="dir">
		<aside class="wa-sidebar">
			<div class="wa-brand-card">
				<div class="wa-brand-mark">WA</div>
				<div>
					<div class="wa-brand-title">Whatapp</div>
					<div class="wa-brand-sub">{{ t("brandSub") }}</div>
				</div>
			</div>

			<div class="wa-status-card">
				<Badge :label="t('externalService')" theme="green" variant="subtle" size="sm" />
				<p>{{ t("externalServiceDesc") }}</p>
			</div>

			<nav class="wa-nav">
				<RouterLink
					v-for="item in navItems"
					:key="item.name"
					:to="item.to"
					class="wa-nav-link"
					:class="{ active: route.name === item.name }"
				>
					<FeatherIcon :name="item.icon" class="wa-nav-icon" />
					<span>{{ item.label }}</span>
				</RouterLink>
			</nav>

			<div class="wa-user-card">
				<div class="wa-user-label">{{ t("session") }}</div>
				<div class="wa-user-name">{{ currentUser }}</div>
				<div class="wa-user-sub">{{ t("sessionSub") }}</div>
			</div>
		</aside>

		<main class="wa-main">
			<header class="wa-header">
				<div>
					<p class="wa-kicker">{{ t("headerKicker") }}</p>
					<h1>{{ navItems.find((item) => item.name === route.name)?.label || "Whatapp" }}</h1>
				</div>
				<div class="wa-header-note">{{ t("headerNote") }}</div>
			</header>

			<RouterView />
			<Toasts />
		</main>
	</div>
</template>

<style>
.wa-shell {
	display: grid;
	grid-template-columns: 300px 1fr;
	min-height: 100vh;
	gap: 24px;
	padding: 24px;
}

.wa-shell[dir="rtl"] {
	grid-template-columns: 1fr 300px;
}

.wa-shell[dir="rtl"] .wa-sidebar {
	order: 2;
}

.wa-shell[dir="rtl"] .wa-main {
	order: 1;
}

.wa-sidebar,
.wa-header,
.wa-panel,
.wa-card,
.wa-message-composer {
	backdrop-filter: blur(18px);
	background: var(--wa-surface);
	border: 1px solid var(--wa-border);
	box-shadow: var(--wa-shadow);
}

.wa-sidebar {
	border-radius: 32px;
	padding: 24px;
	display: flex;
	flex-direction: column;
	gap: 20px;
	position: sticky;
	top: 24px;
	height: calc(100vh - 48px);
}

.wa-brand-card {
	display: flex;
	align-items: center;
	gap: 14px;
	padding: 8px 0 18px;
	border-bottom: 1px solid var(--wa-border);
}

.wa-brand-mark {
	width: 54px;
	height: 54px;
	border-radius: 18px;
	background: linear-gradient(135deg, var(--wa-brand), var(--wa-accent));
	color: white;
	display: grid;
	place-items: center;
	font-weight: 800;
	letter-spacing: 0.08em;
	box-shadow: 0 16px 32px rgba(111, 125, 72, 0.22);
}

.wa-brand-title {
	font-size: 1.35rem;
	font-weight: 800;
	letter-spacing: 0.02em;
}

.wa-brand-sub,
.wa-header-note,
.wa-user-sub,
.wa-status-card p,
.wa-kicker,
.wa-meta,
.wa-empty,
.wa-helper,
.wa-form-help {
	color: var(--wa-muted);
}

.wa-status-card,
.wa-user-card {
	padding: 16px;
	border-radius: var(--wa-radius-sm);
	background: rgba(255, 255, 255, 0.6);
	border: 1px solid var(--wa-border);
}

.wa-status-card p,
.wa-user-card {
	margin: 0;
	line-height: 1.6;
	font-size: 0.92rem;
}

.wa-nav {
	display: flex;
	flex-direction: column;
	gap: 8px;
	flex: 1;
}

.wa-nav-link {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 14px 16px;
	border-radius: 18px;
	color: var(--wa-text);
	text-decoration: none;
	transition: 180ms ease;
	font-weight: 600;
}

.wa-nav-link:hover,
.wa-nav-link.active {
	background: linear-gradient(135deg, rgba(111, 125, 72, 0.14), rgba(217, 143, 92, 0.14));
	transform: translateX(2px);
}

.wa-shell[dir="rtl"] .wa-nav-link:hover,
.wa-shell[dir="rtl"] .wa-nav-link.active {
	transform: translateX(-2px);
}

.wa-nav-icon {
	width: 18px;
	height: 18px;
}

.wa-user-label {
	font-size: 0.8rem;
	text-transform: uppercase;
	letter-spacing: 0.08em;
	color: var(--wa-muted-2);
	margin-bottom: 8px;
}

.wa-user-name {
	font-weight: 700;
	margin-bottom: 6px;
}

.wa-main {
	display: flex;
	flex-direction: column;
	gap: 20px;
	min-width: 0;
}

.wa-header {
	border-radius: 30px;
	padding: 24px 28px;
	display: flex;
	align-items: end;
	justify-content: space-between;
	gap: 16px;
	background:
		linear-gradient(135deg, rgba(111, 125, 72, 0.12), rgba(217, 143, 92, 0.18)),
		var(--wa-surface);
	animation: wa-fade 260ms ease;
}

.wa-header h1,
.wa-panel h2,
.wa-card h3 {
	margin: 0;
	font-weight: 800;
}

.wa-kicker {
	margin: 0 0 6px;
	text-transform: uppercase;
	font-size: 0.8rem;
	letter-spacing: 0.08em;
}

.wa-grid {
	display: grid;
	gap: 18px;
}

.wa-grid.two {
	grid-template-columns: repeat(2, minmax(0, 1fr));
}

.wa-grid.three {
	grid-template-columns: repeat(3, minmax(0, 1fr));
}

.wa-panel,
.wa-card,
.wa-message-composer {
	border-radius: var(--wa-radius);
	padding: 20px;
	animation: wa-fade 300ms ease;
}

.wa-panel-head,
.wa-card-head {
	display: flex;
	justify-content: space-between;
	align-items: start;
	gap: 12px;
	margin-bottom: 18px;
}

.wa-panel-head p,
.wa-card-head p {
	margin: 6px 0 0;
	color: var(--wa-muted);
}

.wa-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
}

.wa-stats {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 12px;
}

.wa-stat {
	padding: 16px;
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.7);
	border: 1px solid var(--wa-border);
}

.wa-stat-label {
	font-size: 0.8rem;
	color: var(--wa-muted-2);
	margin-bottom: 8px;
}

.wa-stat-value {
	font-size: 1.4rem;
	font-weight: 800;
}

.wa-list {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.wa-list-item {
	padding: 16px;
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.72);
	border: 1px solid var(--wa-border);
	transition: 180ms ease;
	cursor: pointer;
}

.wa-list-item:hover,
.wa-list-item.active {
	border-color: var(--wa-border-strong);
	transform: translateY(-1px);
	box-shadow: 0 12px 24px rgba(78, 62, 46, 0.08);
}

.wa-list-title,
.wa-chat-title,
.wa-message-author {
	font-weight: 700;
}

.wa-list-sub,
.wa-chat-sub,
.wa-message-meta {
	font-size: 0.88rem;
	color: var(--wa-muted);
	margin-top: 4px;
}

.wa-chat-layout {
	display: grid;
	grid-template-columns: 360px 1fr;
	gap: 18px;
	min-height: 620px;
}

.wa-chat-list {
	max-height: 720px;
	overflow: auto;
}

.wa-chat-thread {
	display: flex;
	flex-direction: column;
	gap: 16px;
	min-width: 0;
}

.wa-thread-box {
	flex: 1;
	min-height: 0;
	max-height: 560px;
	overflow: auto;
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding-right: 6px;
}

.wa-message {
	padding: 14px 16px;
	border-radius: 18px;
	max-width: 84%;
	background: rgba(255, 255, 255, 0.8);
	border: 1px solid var(--wa-border);
	line-height: 1.6;
}

.wa-message.mine {
	align-self: end;
	background: rgba(111, 125, 72, 0.15);
	border-color: rgba(111, 125, 72, 0.24);
}

.wa-message-body {
	white-space: pre-wrap;
	word-break: break-word;
	margin-top: 8px;
}

.wa-message-composer {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.wa-form-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 14px;
}

.wa-form-grid.single {
	grid-template-columns: 1fr;
}

.wa-form-actions {
	display: flex;
	justify-content: end;
	gap: 10px;
	margin-top: 8px;
}

.wa-toggle-list {
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding: 14px 16px;
	border: 1px dashed var(--wa-border-strong);
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.58);
}

.wa-toggle {
	display: flex;
	align-items: center;
	gap: 10px;
	font-weight: 600;
	color: var(--wa-text);
}

.wa-toggle input {
	accent-color: var(--wa-brand-strong);
	width: 16px;
	height: 16px;
}

.wa-inline {
	display: flex;
	gap: 10px;
	align-items: end;
	flex-wrap: wrap;
}

.wa-empty {
	padding: 22px;
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.58);
	border: 1px dashed var(--wa-border-strong);
	text-align: center;
}

.wa-code {
	font-size: 2rem;
	font-weight: 800;
	letter-spacing: 0.16em;
	color: var(--wa-brand-strong);
	text-align: center;
	padding: 18px;
	border-radius: 18px;
	background: rgba(111, 125, 72, 0.1);
	border: 1px solid rgba(111, 125, 72, 0.2);
}

.wa-qr {
	max-width: 240px;
	width: 100%;
	border-radius: 22px;
	border: 1px solid var(--wa-border);
	background: white;
	padding: 12px;
	align-self: center;
}

.wa-badge {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 10px;
	border-radius: 999px;
	font-size: 0.8rem;
	font-weight: 700;
	background: rgba(111, 125, 72, 0.12);
	color: var(--wa-brand-strong);
}

.wa-badge.warn {
	background: rgba(217, 143, 92, 0.16);
	color: #9f5c2e;
}

.wa-badge.danger {
	background: rgba(187, 81, 66, 0.14);
	color: var(--wa-danger);
}

.wa-badge.success {
	background: rgba(47, 143, 91, 0.15);
	color: var(--wa-success);
}

@keyframes wa-fade {
	from {
		opacity: 0;
		transform: translateY(10px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

@media (max-width: 1100px) {
	.wa-shell,
	.wa-chat-layout,
	.wa-grid.two,
	.wa-grid.three,
	.wa-stats,
	.wa-form-grid {
		grid-template-columns: 1fr;
	}

	.wa-sidebar {
		position: static;
		height: auto;
	}

	.wa-header {
		flex-direction: column;
		align-items: start;
	}
}
</style>