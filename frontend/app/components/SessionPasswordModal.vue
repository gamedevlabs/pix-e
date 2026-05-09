/**
 * Modal for re-establishing the session encryption key when it expires.
 *
 * The encryption key protecting stored API keys expires periodically (every hour).
 * This dialog prompts the user for their password to re-establish it.
 * After successful unlock, the pending API request is automatically retried.
 *
 * @emits success - Emitted after the encryption key is successfully re-established.
 * @emits close   - Emitted when the modal is dismissed without unlocking.
 */
<script setup lang="ts">
const emit = defineEmits<{
  success: []
  close: []
  openSettings: []
}>()

const password = ref('')
const isSubmitting = ref(false)
const error = ref('')
const { reestablish, dismissModal, showPasswordModal } = getSessionKey()

async function handleSubmit() {
  if (!password.value) return
  isSubmitting.value = true
  error.value = ''
  const result = await reestablish(password.value)
  if (result.ok) {
    password.value = ''
    emit('success')
  } else {
    error.value = result.error || 'Wrong password'
    if (result.openSettings) {
      emit('openSettings')
    }
  }
  isSubmitting.value = false
}

function handleClose() {
  dismissModal()
  emit('close')
}
</script>

<template>
  <UModal
    v-model:open="showPasswordModal"
    title="Encryption Key Expired"
    description="Your encryption key expired for security. Enter your password to re-enable API key access."
    :dismissible="true"
    class="max-w-sm w-full"
    @close="handleClose"
  >
    <template #body>
      <div class="space-y-4">
        <p class="text-sm text-dimmed">
          The encryption key that protects your API keys expires every hour. Enter your password to
          refresh it.
        </p>
        <UInput
          v-model="password"
          type="password"
          placeholder="Your password"
          size="lg"
          @keyup.enter="handleSubmit"
        />
        <p v-if="error" class="text-xs text-error">{{ error }}</p>
        <div class="flex justify-end">
          <UButton :loading="isSubmitting" @click="handleSubmit"> Unlock </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
