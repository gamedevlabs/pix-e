<script setup lang="ts">
import type { CreateApiKeyPayload, ProviderType, UserApiKey } from '~/types/api-key'
import { PROVIDER_OPTIONS } from '~/utils/api-key'
import { useApiKeysApi } from '~/composables/api/apiKeysApi'

const emit = defineEmits<{
  close: []
  created: [key: UserApiKey]
  showMorpheusHelp: []
}>()

const { createKey } = useApiKeysApi()
const toast = useToast()

const formStep = ref<'provider' | 'details'>('provider')
const formProvider = ref<string | null>(null)
const formLabel = ref('')
const formKey = ref('')
const formBaseUrl = ref('')
const isSubmitting = ref(false)
const formError = ref('')

const isCustom = computed(() => formProvider.value === 'custom')

function reset() {
  formStep.value = 'provider'
  formProvider.value = null
  formLabel.value = ''
  formKey.value = ''
  formBaseUrl.value = ''
  formError.value = ''
  isSubmitting.value = false
}

async function handleSubmit() {
  if (!formProvider.value || !formLabel.value || !formKey.value) return
  if (isCustom.value && !formBaseUrl.value) return
  isSubmitting.value = true
  formError.value = ''
  try {
    const body: CreateApiKeyPayload = {
      provider: formProvider.value as ProviderType,
      label: formLabel.value,
      key: formKey.value,
    }
    if (isCustom.value) {
      body.base_url = formBaseUrl.value
    }
    const result = await createKey(body)
    emit('created', result)
    reset()
    toast.add({ title: 'API key saved', color: 'success' })
  } catch (err: unknown) {
    const e = err as Record<string, unknown>
    const data = e?.data as Record<string, unknown> | undefined
    const detail = data?.detail as string | undefined
    const keyErr = data?.key as string | string[] | undefined
    const baseUrlErr = data?.base_url as string | string[] | undefined
    const firstFieldErr =
      (Array.isArray(keyErr) && keyErr[0]) ||
      (typeof keyErr === 'string' && keyErr) ||
      (Array.isArray(baseUrlErr) && baseUrlErr[0]) ||
      (typeof baseUrlErr === 'string' && baseUrlErr)
    formError.value =
      (typeof detail === 'string' && detail) || firstFieldErr || 'Failed to save key'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="mb-4 p-4 border rounded-lg">
    <div class="flex items-center justify-between mb-3">
      <h4 class="font-medium">
        {{ formStep === 'provider' ? 'Select Provider' : 'Key Details' }}
      </h4>
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-x"
        size="xs"
        @click="$emit('close')"
      />
    </div>

    <div v-if="formStep === 'provider'" class="space-y-3">
      <div class="grid grid-cols-2 gap-2">
        <div
          v-for="opt in PROVIDER_OPTIONS"
          :key="opt.value"
          class="relative p-3 rounded-lg border cursor-pointer hover:border-primary transition-colors text-center"
          :class="formProvider === opt.value ? 'border-primary bg-primary/5' : 'border-default'"
          @click="formProvider = opt.value"
        >
          <template v-if="opt.value === 'morpheus'">
            <span
              class="absolute -top-1.5 -left-1.5 bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md leading-tight"
            >
              FREE
            </span>
            <UButton
              icon="i-lucide-circle-help"
              variant="ghost"
              color="neutral"
              size="xs"
              class="absolute top-0.5 right-0.5"
              @click.stop="$emit('showMorpheusHelp')"
            />
          </template>
          <UIcon :name="opt.icon" class="size-6 mx-auto mb-1" />
          <div class="text-xs font-medium">{{ opt.label }}</div>
        </div>
      </div>
      <div class="flex justify-end">
        <UButton size="sm" :disabled="!formProvider" @click="formStep = 'details'">
          Continue
        </UButton>
      </div>
    </div>

    <div v-else class="space-y-3">
      <UInput v-model="formLabel" placeholder="Label (e.g. My Work Key)" size="sm" />
      <div class="flex items-center gap-1 text-xs">
        <UInput
          v-model="formKey"
          type="password"
          size="sm"
          class="flex-1"
          :placeholder="
            {
              openai: 'sk-...',
              gemini: 'AIza...',
              morpheus: 'sk-...',
              custom: 'Enter API key',
            }[formProvider ?? 'openai']
          "
        />
        <UButton
          v-if="formProvider === 'morpheus'"
          icon="i-lucide-circle-help"
          variant="ghost"
          color="neutral"
          size="xs"
          class="mt-0.5 shrink-0"
          @click="$emit('showMorpheusHelp')"
          >how can i get a free api key?</UButton
        >
      </div>
      <template v-if="isCustom">
        <UInput v-model="formBaseUrl" placeholder="https://api.openai.com/v1" size="sm" />
        <p class="text-xs text-dimmed -mt-1">
          API base URL (e.g. https://opencode.ai/zen/go/v1 — <b>not</b> the /chat/completions path)
        </p>
      </template>
      <p v-if="formError" class="text-xs text-error">{{ formError }}</p>
      <div class="flex justify-between pt-1">
        <UButton variant="ghost" size="sm" @click="formStep = 'provider'"> Back </UButton>
        <UButton
          size="sm"
          :loading="isSubmitting"
          :disabled="!formLabel || !formKey || (isCustom && !formBaseUrl)"
          @click="handleSubmit"
        >
          Save Key
        </UButton>
      </div>
    </div>
  </div>
</template>
