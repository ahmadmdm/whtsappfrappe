<script setup>
import { computed, onMounted, ref } from "vue"
import { Button, Input } from "frappe-ui"
import { call } from "@/lib/api"
import { useLocale } from "@/lib/i18n"
import { notifyError, notifySuccess } from "@/lib/notify"

const { t } = useLocale()

const loading = ref(false)
const bootstrap = ref(null)
const selectedDevice = ref("")
const newDeviceId = ref("")
const pairPhone = ref("")
const pairCode = ref("")
const qrLink = ref("")
const qrDuration = ref(null)

const devices = computed(() => bootstrap.value?.devices || [])
const serviceReady = computed(() => Boolean(bootstrap.value?.settings?.base_url))
const serviceError = computed(() => bootstrap.value?.service_error || "")
const serviceAvailable = computed(() => serviceReady.value && !serviceError.value)
const selectedDeviceInfo = computed(
	() => devices.value.find((device) => device.id === selectedDevice.value) || null
)

function stateClass(state) {
	if (state === "logged_in" || state === "connected") return "success"
	if (state === "connecting") return "warn"
	return "danger"
}

async function load() {
	loading.value = true
	try {
		const data = await call("whatapp.api.get_bootstrap")
		bootstrap.value = data
		if (!selectedDevice.value && data.default_device_id) {
			selectedDevice.value = data.default_device_id
		}
		if (!selectedDevice.value && data.devices?.length) {
			selectedDevice.value = data.devices[0].id
		}
	} catch (error) {
		notifyError(error.message)
	} finally {
		loading.value = false
	}
}

async function createDevice() {
	if (!serviceAvailable.value) {
		notifyError(serviceError.value || t("serviceUnavailableAction"))
		return
	}
	try {
		const result = await call("whatapp.api.create_device", { device_id: newDeviceId.value })
		notifySuccess(result.message || t("deviceCreated"))
		newDeviceId.value = ""
		selectedDevice.value = result.device?.id || selectedDevice.value
		await load()
	} catch (error) {
		notifyError(error.message)
	}
}

async function runAction(method, args = {}, successMessage = t("actionCompleted")) {
	if (!serviceAvailable.value) {
		notifyError(serviceError.value || t("serviceUnavailableAction"))
		return
	}
	try {
		const result = await call(method, args)
		if (result.qr_link) {
			qrLink.value = result.qr_link
			qrDuration.value = result.qr_duration
		}
		if (result.pair_code) {
			pairCode.value = result.pair_code
		}
		notifySuccess(result.message || successMessage)
		await load()
	} catch (error) {
		notifyError(error.message)
	}
}

onMounted(load)
</script>

<template>
	<section class="wa-grid two">
		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("serviceControl") }}</h2>
					<p>{{ t("serviceControlDesc") }}</p>
				</div>
				<Button variant="outline" @click="load" :loading="loading">{{ t("refresh") }}</Button>
			</div>

			<div class="wa-stats">
				<div class="wa-stat">
					<div class="wa-stat-label">{{ t("serviceUrl") }}</div>
					<div class="wa-stat-value">{{ serviceReady ? t("configured") : t("missing") }}</div>
				</div>
				<div class="wa-stat">
					<div class="wa-stat-label">{{ t("trackedDevices") }}</div>
					<div class="wa-stat-value">{{ devices.length }}</div>
				</div>
				<div class="wa-stat">
					<div class="wa-stat-label">{{ t("webhookTarget") }}</div>
					<div class="wa-stat-value">{{ bootstrap?.webhook_url ? t("ready") : t("configure") }}</div>
				</div>
			</div>

			<div v-if="bootstrap?.service_error" class="wa-empty" style="margin-top: 18px">
				{{ bootstrap.service_error }}
			</div>

			<div class="wa-panel" style="margin-top: 18px; padding: 16px; background: rgba(255,255,255,0.55)">
				<div class="wa-panel-head" style="margin-bottom: 12px">
					<div>
						<h2 style="font-size: 1rem">{{ t("createDeviceTitle") }}</h2>
						<p>{{ t("createDeviceDesc") }}</p>
					</div>
				</div>
				<div class="wa-inline">
					<Input v-model="newDeviceId" :label="t('deviceId')" :placeholder="t('optional')" />
					<Button variant="solid" @click="createDevice" :disabled="!serviceAvailable">{{ t("create") }}</Button>
				</div>
			</div>
		</div>

		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("pairingWorkflows") }}</h2>
					<p>{{ t("pairingDesc") }}</p>
				</div>
			</div>

			<div class="wa-form-grid single">
				<Input
					v-model="selectedDevice"
					:label="t('selectedDevice')"
					:placeholder="t('selectedDevicePlaceholder')"
				/>
				<div v-if="serviceError" class="wa-form-help">{{ t("serviceUnavailableHint") }}</div>
				<div class="wa-actions">
					<Button variant="solid" @click="runAction('whatapp.api.request_login_qr', { device_id: selectedDevice }, t('qrGenerated'))" :disabled="!selectedDevice || !serviceAvailable">{{ t("generateQr") }}</Button>
					<Button variant="outline" @click="runAction('whatapp.api.request_logout', { device_id: selectedDevice }, t('logoutRequested'))" :disabled="!selectedDevice || !serviceAvailable">{{ t("logout") }}</Button>
					<Button variant="outline" @click="runAction('whatapp.api.request_reconnect', { device_id: selectedDevice }, t('reconnectRequested'))" :disabled="!selectedDevice || !serviceAvailable">{{ t("reconnect") }}</Button>
				</div>

				<div class="wa-inline">
					<Input v-model="pairPhone" :label="t('pairPhone')" placeholder="+9665..." />
					<Button
						variant="outline"
						@click="runAction('whatapp.api.request_pair_code', { device_id: selectedDevice, phone: pairPhone }, t('pairCodeGenerated'))"
						:disabled="!selectedDevice || !pairPhone || !serviceAvailable"
					>
						{{ t("generatePairCode") }}
					</Button>
				</div>
			</div>

			<div v-if="pairCode" class="wa-code">{{ pairCode }}</div>
			<img v-if="qrLink" :src="qrLink" class="wa-qr" alt="WhatsApp QR" />
			<div v-if="qrDuration" class="wa-helper">{{ t("qrValidity", qrDuration) }}</div>
		</div>
	</section>

	<section class="wa-grid two">
		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("devices") }}</h2>
					<p>{{ t("devicesDesc") }}</p>
				</div>
			</div>

			<div v-if="!devices.length" class="wa-empty">{{ t("noDevices") }}</div>
			<div v-else class="wa-list">
				<div
					v-for="device in devices"
					:key="device.id"
					class="wa-list-item"
					:class="{ active: selectedDevice === device.id }"
					@click="selectedDevice = device.id"
				>
					<div class="wa-panel-head" style="margin-bottom: 0">
						<div>
							<div class="wa-list-title">{{ device.id }}</div>
							<div class="wa-list-sub">{{ device.display_name || device.phone_number || t('noDisplayName') }}</div>
						</div>
						<span class="wa-badge" :class="stateClass(device.state)">{{ device.state || t('unknownLower') }}</span>
					</div>
					<div class="wa-meta">{{ device.jid || t('noJidYet') }}</div>
				</div>
			</div>
		</div>

		<div class="wa-panel">
			<div class="wa-panel-head">
				<div>
					<h2>{{ t("selectedDeviceTitle") }}</h2>
					<p>{{ t("selectedDeviceDesc") }}</p>
				</div>
			</div>

			<div v-if="!selectedDeviceInfo" class="wa-empty">{{ t("chooseDeviceDetails") }}</div>
			<div v-else class="wa-list">
				<div class="wa-list-item" style="cursor: default">
					<div class="wa-list-title">{{ selectedDeviceInfo.id }}</div>
					<div class="wa-list-sub">{{ selectedDeviceInfo.display_name || selectedDeviceInfo.phone_number || t('noDisplayName') }}</div>
					<div class="wa-meta" style="margin-top: 12px">{{ t("createdAt") }}: {{ selectedDeviceInfo.created_at || t('unknown') }}</div>
					<div class="wa-meta">{{ t("jid") }}: {{ selectedDeviceInfo.jid || t('jidUnavailable') }}</div>
					<div class="wa-meta">{{ t("state") }}: {{ selectedDeviceInfo.state || t('unknown') }}</div>
				</div>
			</div>
		</div>
	</section>
</template>