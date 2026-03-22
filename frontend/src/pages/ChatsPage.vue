<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { Button, Input } from "frappe-ui"
import { call } from "@/lib/api"
import { useLocale } from "@/lib/i18n"
import { notifyError, notifySuccess } from "@/lib/notify"

const { t } = useLocale()

const bootstrap = ref(null)
const selectedDevice = ref("")
const selectedChat = ref("")
const search = ref("")
const outgoingMessage = ref("")
const loadingChats = ref(false)
const loadingMessages = ref(false)
const chatsData = ref({ data: [] })
const messagesData = ref({ data: [] })

const chats = computed(() => chatsData.value?.data || chatsData.value?.results?.data || [])
const messages = computed(() => messagesData.value?.data || messagesData.value?.results?.data || [])
const serviceError = computed(() => bootstrap.value?.service_error || "")
const serviceAvailable = computed(() => Boolean(bootstrap.value?.settings?.base_url) && !serviceError.value)
const selectedChatInfo = computed(() => chats.value.find((chat) => chat.chat_jid === selectedChat.value) || null)

async function loadBootstrap() {
	try {
		bootstrap.value = await call("whatapp.api.get_bootstrap")
		if (!selectedDevice.value) {
			selectedDevice.value = bootstrap.value?.default_device_id || bootstrap.value?.devices?.[0]?.id || ""
		}
	} catch (error) {
		notifyError(error.message)
	}
}

async function loadChats() {
	if (!selectedDevice.value || !serviceAvailable.value) {
		if (serviceError.value) {
			notifyError(serviceError.value)
		}
		return
	}
	loadingChats.value = true
	try {
		const data = await call("whatapp.api.list_chats", {
			device_id: selectedDevice.value,
			search: search.value,
			limit: 40,
		})
		chatsData.value = data
		if (!selectedChat.value && chats.value.length) {
			selectedChat.value = chats.value[0].chat_jid
		}
	} catch (error) {
		notifyError(error.message)
	} finally {
		loadingChats.value = false
	}
}

async function loadMessages() {
	if (!selectedDevice.value || !selectedChat.value || !serviceAvailable.value) {
		if (serviceError.value) {
			notifyError(serviceError.value)
		}
		return
	}
	loadingMessages.value = true
	try {
		messagesData.value = await call("whatapp.api.get_chat_messages", {
			device_id: selectedDevice.value,
			chat_jid: selectedChat.value,
			limit: 60,
		})
	} catch (error) {
		notifyError(error.message)
	} finally {
		loadingMessages.value = false
	}
}

async function sendText() {
	if (!selectedDevice.value || !selectedChat.value || !outgoingMessage.value.trim() || !serviceAvailable.value) {
		if (serviceError.value) {
			notifyError(serviceError.value)
		}
		return
	}
	try {
		await call("whatapp.api.send_text_message", {
			device_id: selectedDevice.value,
			phone: selectedChat.value,
			message: outgoingMessage.value.trim(),
		})
		notifySuccess(t("messageSent"))
		outgoingMessage.value = ""
		await loadMessages()
	} catch (error) {
		notifyError(error.message)
	}
}

watch(selectedChat, loadMessages)
watch(selectedDevice, async () => {
	selectedChat.value = ""
	await loadChats()
})

onMounted(async () => {
	await loadBootstrap()
	await loadChats()
	await loadMessages()
})
</script>

<template>
	<section class="wa-panel">
		<div class="wa-panel-head">
			<div>
				<h2>{{ t("chatBrowser") }}</h2>
				<p>{{ t("chatBrowserDesc") }}</p>
			</div>
			<div class="wa-actions">
				<Button variant="outline" @click="loadChats" :loading="loadingChats">{{ t("refreshChats") }}</Button>
				<Button variant="outline" @click="loadMessages" :loading="loadingMessages" :disabled="!selectedChat">{{ t("refreshThread") }}</Button>
			</div>
		</div>

		<div class="wa-inline" style="margin-bottom: 18px">
			<Input v-model="selectedDevice" :label="t('deviceId')" :placeholder="t('required')" />
			<Input v-model="search" :label="t('searchChats')" :placeholder="t('searchChatsPlaceholder')" />
			<Button variant="solid" @click="loadChats" :disabled="!serviceAvailable">{{ t("search") }}</Button>
		</div>

		<div v-if="serviceError" class="wa-empty" style="margin-bottom: 18px">{{ serviceError }}</div>

		<div class="wa-chat-layout">
			<div class="wa-panel wa-chat-list">
				<div v-if="!serviceAvailable" class="wa-empty">{{ t("serviceUnavailableHint") }}</div>
				<div v-else-if="!chats.length" class="wa-empty">{{ t("noChatsReturned") }}</div>
				<div v-else class="wa-list">
					<div
						v-for="chat in chats"
						:key="chat.chat_jid"
						class="wa-list-item"
						:class="{ active: selectedChat === chat.chat_jid }"
						@click="selectedChat = chat.chat_jid"
					>
						<div class="wa-chat-title">{{ chat.chat_name || chat.push_name || chat.chat_jid }}</div>
						<div class="wa-chat-sub">{{ chat.chat_jid }}</div>
						<div class="wa-chat-sub">{{ chat.last_message?.text || chat.last_message || t('noPreview') }}</div>
					</div>
				</div>
			</div>

			<div class="wa-chat-thread">
				<div class="wa-panel">
					<div class="wa-panel-head">
						<div>
							<h2>{{ selectedChatInfo?.chat_name || selectedChatInfo?.push_name || t('conversation') }}</h2>
							<p>{{ selectedChatInfo?.chat_jid || t('selectChatFirst') }}</p>
						</div>
					</div>

					<div v-if="!selectedChat" class="wa-empty">{{ t("selectChatLeft") }}</div>
					<div v-else-if="!serviceAvailable" class="wa-empty">{{ t("serviceUnavailableHint") }}</div>
					<div v-else class="wa-thread-box">
						<div v-if="!messages.length" class="wa-empty">{{ t("noMessagesReturned") }}</div>
						<div
							v-for="message in messages"
							:key="message.id || message.message_id || message.timestamp"
							class="wa-message"
							:class="{ mine: message.is_from_me }"
						>
							<div class="wa-message-author">{{ message.from_name || message.push_name || message.from || t('unknownSender') }}</div>
							<div class="wa-message-meta">{{ message.timestamp || message.created_at || t('noTime') }}</div>
							<div class="wa-message-body">{{ message.body || message.text || t('noTextBody') }}</div>
						</div>
					</div>
				</div>

				<div class="wa-message-composer">
					<Input v-model="outgoingMessage" :label="t('reply')" :placeholder="t('replyPlaceholder')" />
					<div class="wa-form-actions">
						<Button variant="solid" @click="sendText" :disabled="!selectedChat || !outgoingMessage.trim() || !serviceAvailable">{{ t("sendText") }}</Button>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>