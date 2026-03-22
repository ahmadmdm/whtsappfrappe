<script setup>
import { onMounted, reactive, ref } from "vue"
import { Button, Input } from "frappe-ui"
import { call } from "@/lib/api"
import { useLocale } from "@/lib/i18n"
import { notifyError, notifySuccess } from "@/lib/notify"

const origin = window.location.origin
const userSettingsPath = "/app/whatapp-user-notification-setting"
const { t } = useLocale()

const loading = ref(false)
const saving = ref(false)
const usersLoading = ref(false)
const usersSaving = ref(false)
const notificationUsers = ref([])

const form = reactive({
	service_url: "",
	basic_auth_username: "",
	basic_auth_password: "",
	default_device_id: "",
	notification_forwarding_enabled: 0,
	notification_default_device_id: "",
	notification_allowed_types: "",
	notification_skip_own: 1,
	notification_include_link: 1,
	notification_include_content: 0,
	notification_include_sender: 1,
	notification_max_length: 1000,
	notification_message_template: "",
	webhook_secret: "",
	webhook_events: "message,message.ack",
	request_timeout: 45,
	enabled: 1,
	notes: "",
})

async function load() {
	loading.value = true
	try {
		const data = await call("whatapp.api.get_settings")
		Object.assign(form, data)
	} catch (error) {
		notifyError(error.message)
	} finally {
		loading.value = false
	}
}

async function loadNotificationUsers() {
	usersLoading.value = true
	try {
		const response = await call("whatapp.api.list_notification_users")
		notificationUsers.value = (response.data || []).map((row) => ({ ...row }))
	} catch (error) {
		notifyError(error.message)
	} finally {
		usersLoading.value = false
	}
}

async function save() {
	saving.value = true
	try {
		await call("whatapp.api.save_settings", { payload: JSON.stringify(form) })
		notifySuccess(t("settingsSaved"))
		await load()
	} catch (error) {
		notifyError(error.message)
	} finally {
		saving.value = false
	}
}

function openUserSettings() {
	window.location.href = userSettingsPath
}

function useSystemPhone(row) {
	row.phone_number = row.system_phone || ""
	row.enabled = row.phone_number ? 1 : row.enabled
}

async function saveNotificationUsers() {
	usersSaving.value = true
	try {
		const payload = notificationUsers.value.map((row) => ({
			user: row.user,
			enabled: row.enabled ? 1 : 0,
			phone_number: row.phone_number || "",
			device_id: row.device_id || "",
			allowed_notification_types: row.allowed_notification_types || "",
		}))
		await call("whatapp.api.save_notification_users", { payload: JSON.stringify(payload) })
		notifySuccess(t("notificationUsersSaved"))
		await loadNotificationUsers()
	} catch (error) {
		notifyError(error.message)
	} finally {
		usersSaving.value = false
	}
}

onMounted(async () => {
	await Promise.all([load(), loadNotificationUsers()])
})
</script>

<template>
	<section class="wa-grid two">
		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("connectionSettings") }}</h2>
					<p>{{ t("connectionSettingsDesc") }}</p>
				</div>
				<Button variant="outline" @click="load" :loading="loading">{{ t("reload") }}</Button>
			</div>

			<div class="wa-form-grid">
				<Input v-model="form.service_url" :label="t('serviceUrl')" placeholder="http://127.0.0.1:3000" />
				<Input v-model="form.default_device_id" :label="t('defaultDeviceId')" :placeholder="t('optional')" />
				<Input v-model="form.basic_auth_username" :label="t('basicAuthUsername')" :placeholder="t('optional')" />
				<Input v-model="form.basic_auth_password" :label="t('basicAuthPassword')" type="password" :placeholder="t('leaveBlankKeepCurrent')" />
				<Input v-model="form.webhook_secret" :label="t('webhookSecret')" type="password" :placeholder="t('leaveBlankKeepCurrent')" />
				<Input v-model="form.request_timeout" :label="t('timeoutSeconds')" type="number" placeholder="45" />
			</div>

			<div class="wa-form-grid single" style="margin-top: 14px">
				<Input v-model="form.webhook_events" :label="t('webhookEvents')" placeholder="message,message.ack" />

				<div style="padding-top: 4px">
					<div class="wa-list-title">{{ t("notificationDeliveryTitle") }}</div>
					<p class="wa-form-help" style="margin-top: 8px">{{ t("notificationDeliveryDesc") }}</p>
				</div>

				<div class="wa-form-grid">
					<div class="wa-toggle-list">
						<label class="wa-toggle">
							<input v-model="form.notification_forwarding_enabled" type="checkbox" :true-value="1" :false-value="0" />
							<span>{{ t("forwardUserNotifications") }}</span>
						</label>
						<label class="wa-toggle">
							<input v-model="form.notification_skip_own" type="checkbox" :true-value="1" :false-value="0" />
							<span>{{ t("notificationSkipOwn") }}</span>
						</label>
						<label class="wa-toggle">
							<input v-model="form.notification_include_link" type="checkbox" :true-value="1" :false-value="0" />
							<span>{{ t("notificationIncludeLink") }}</span>
						</label>
						<label class="wa-toggle">
							<input v-model="form.notification_include_content" type="checkbox" :true-value="1" :false-value="0" />
							<span>{{ t("notificationIncludeContent") }}</span>
						</label>
						<label class="wa-toggle">
							<input v-model="form.notification_include_sender" type="checkbox" :true-value="1" :false-value="0" />
							<span>{{ t("notificationIncludeSender") }}</span>
						</label>
					</div>

					<div class="wa-form-grid single">
						<Input v-model="form.notification_default_device_id" :label="t('notificationDeviceId')" :placeholder="t('optional')" />
						<Input v-model="form.notification_allowed_types" :label="t('notificationTypes')" placeholder="Mention,Assignment,Alert" />
						<Input v-model="form.notification_max_length" :label="t('notificationMaxLength')" type="number" placeholder="1000" />
					</div>
				</div>

				<div>
					<label class="wa-kicker" style="display:block;margin-bottom:8px">{{ t("notificationTemplate") }}</label>
					<textarea
						v-model="form.notification_message_template"
						rows="5"
						style="width:100%;border:1px solid var(--wa-border);border-radius:18px;padding:14px 16px;background:rgba(255,255,255,0.88);resize:vertical;color:var(--wa-text)"
						:placeholder="t('notificationTemplatePlaceholder')"
					/>
					<div class="wa-form-help" style="margin-top: 8px">{{ t("templateKeysHelp") }}</div>
				</div>

				<div>
					<label class="wa-kicker" style="display:block;margin-bottom:8px">{{ t("notes") }}</label>
					<textarea
						v-model="form.notes"
						rows="5"
						style="width:100%;border:1px solid var(--wa-border);border-radius:18px;padding:14px 16px;background:rgba(255,255,255,0.88);resize:vertical;color:var(--wa-text)"
						:placeholder="t('notesPlaceholder')"
					/>
				</div>
			</div>

			<div class="wa-form-actions">
				<Button variant="solid" @click="save" :loading="saving">{{ t("saveSettings") }}</Button>
			</div>
		</div>

		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("webhookTargetTitle") }}</h2>
					<p>{{ t("webhookTargetDesc") }}</p>
				</div>
			</div>

			<div class="wa-code" style="font-size: 1rem; letter-spacing: 0.02em; text-align: start">
				{{ origin }}/api/method/whatapp.api.receive_webhook
			</div>

			<div class="wa-empty" style="text-align: start">
				<div class="wa-list-title">{{ t("suggestedEnv") }}</div>
				<div class="wa-form-help" style="margin-top: 10px">WHATSAPP_WEBHOOK={{ origin }}/api/method/whatapp.api.receive_webhook</div>
				<div class="wa-form-help">WHATSAPP_WEBHOOK_SECRET=&lt;same secret from settings&gt;</div>
				<div class="wa-form-help">WHATSAPP_WEBHOOK_EVENTS={{ form.webhook_events || 'message,message.ack' }}</div>
			</div>

			<div class="wa-empty" style="text-align: start; margin-top: 14px">
				<div class="wa-list-title">{{ t("userRulesTitle") }}</div>
				<p class="wa-form-help" style="margin-top: 10px">{{ t("userRulesDesc") }}</p>
				<div class="wa-form-help">{{ t("phoneFallbackHelp") }}</div>
				<div class="wa-form-actions" style="justify-content: start; margin-top: 14px">
					<Button variant="outline" @click="openUserSettings">{{ t("openUserRules") }}</Button>
				</div>
			</div>

			<div class="wa-empty" style="text-align: start; margin-top: 14px">
				<div class="wa-panel-head" style="margin-bottom: 14px">
					<div>
						<div class="wa-list-title">{{ t("notificationUsersTitle") }}</div>
						<p class="wa-form-help" style="margin-top: 10px">{{ t("notificationUsersDesc") }}</p>
					</div>
					<Button variant="outline" @click="loadNotificationUsers" :loading="usersLoading">{{ t("fetchSystemUsers") }}</Button>
				</div>

				<div v-if="usersLoading && !notificationUsers.length" class="wa-form-help">{{ t("loadingUsers") }}</div>
				<div v-else-if="!notificationUsers.length" class="wa-form-help">{{ t("noSystemUsers") }}</div>
				<div v-else style="display:grid;gap:12px;max-height:620px;overflow:auto;padding-right:2px">
					<div v-for="row in notificationUsers" :key="row.user" class="wa-list-item" style="cursor:default">
						<div class="wa-panel-head" style="margin-bottom: 10px">
							<div>
								<div class="wa-list-title">{{ row.full_name }}</div>
								<div class="wa-list-sub">{{ row.user }}</div>
							</div>
							<label class="wa-toggle" style="margin:0">
								<input v-model="row.enabled" type="checkbox" :true-value="1" :false-value="0" />
								<span>{{ t("enabledLabel") }}</span>
							</label>
						</div>

						<div class="wa-form-help" style="margin-bottom: 10px">
							{{ t("systemPhoneLabel") }}: {{ row.system_phone || t("missing") }}
						</div>

						<div class="wa-form-grid single">
							<Input v-model="row.phone_number" :label="t('notificationPhoneNumber')" :placeholder="row.system_phone || t('optional')" />
							<Input v-model="row.device_id" :label="t('notificationDeviceOverride')" :placeholder="form.notification_default_device_id || t('optional')" />
						</div>

						<div class="wa-form-actions" style="justify-content: start; margin-top: 10px">
							<Button variant="outline" @click="useSystemPhone(row)" :disabled="!row.system_phone">{{ t("useSystemPhone") }}</Button>
						</div>

						<div v-if="row.last_delivery_on" class="wa-form-help" style="margin-top: 10px">
							{{ t("lastDeliveryOn") }}: {{ row.last_delivery_on }}
						</div>
						<div v-if="row.last_error" class="wa-form-help" style="margin-top: 6px; color:#9f1239">
							{{ t("lastErrorLabel") }}: {{ row.last_error }}
						</div>
					</div>
				</div>

				<div class="wa-form-actions" style="justify-content: start; margin-top: 14px">
					<Button variant="solid" @click="saveNotificationUsers" :loading="usersSaving">{{ t("saveNotificationUsers") }}</Button>
				</div>
			</div>
		</div>
	</section>
</template>