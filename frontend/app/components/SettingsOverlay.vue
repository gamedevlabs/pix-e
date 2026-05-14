/**
 * Settings overlay modal for managing personal API keys.
 *
 * Allows users to add, edit, and delete API keys for LLM providers
 * (OpenAI, Gemini, Morpheus, or custom OpenAI-compatible endpoints).
 * Keys are encrypted at rest.
 *
 * The add flow is two-step: first select a provider, then fill in key details.
 * Existing keys can be toggled active/inactive.
 * Edit mode allows updating the label, base URL, and active state.
 */
<script setup lang="ts">
import type {
  CreateApiKeyPayload,
  ProviderType,
  UpdateApiKeyPayload,
  UserApiKey,
} from '~/types/api-key'
import { PROVIDER_ICONS, PROVIDER_LABELS, PROVIDER_OPTIONS } from '~/utils/api-key'
import { SessionExpiredError } from '~/utils/sessionFetch'
import { getSessionKey } from '~/composables/useSessionKey'
import { useApiKeysApi } from '~/composables/api/apiKeysApi'

const open = defineModel<boolean>('open', { default: false })
const llmStore = useLLM()

const { fetchKeys, createKey, updateKey, deleteKey, testKey } = useApiKeysApi()
const keys = ref<UserApiKey[]>([])
const toast = useToast()

// Add form state
const showAddForm = ref(false)
const formStep = ref<'provider' | 'details'>('provider')
const formProvider = ref<string | null>(null)
const formLabel = ref('')
const formKey = ref('')
const formBaseUrl = ref('')
const isSubmitting = ref(false)
const formError = ref('')
const deletingId = ref<string | null>(null)
const testingId = ref<string | null>(null)

// Edit state
const editingId = ref<string | null>(null)
const editLabel = ref('')
const editBaseUrl = ref('')
const editIsActive = ref(true)
const editKeyValue = ref('')
const isEditing = ref(false)

// Help modals
const showMorpheusHelp = ref(false)

const isCustom = computed(() => formProvider.value === 'custom')
const isEditCustom = computed(() => {
  const key = keys.value.find((k) => k.id === editingId.value)
  return key?.provider === 'custom'
})

watch(open, async (val) => {
  if (val) {
    try {
      keys.value = await fetchKeys()
    } catch {
      /* */
    }
    try {
      await llmStore.refreshModels()
    } catch {
      getSessionKey().handleSessionExpired(() => llmStore.refreshModels())
    }
  }
})

// === Add form ===

function resetForm() {
  showAddForm.value = false
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
    keys.value.push(result)
    resetForm()
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
      (typeof detail === 'string' && detail) ||
      firstFieldErr ||
      'Failed to save key'
  } finally {
    isSubmitting.value = false
  }
}

// === Edit form ===

function startEdit(key: UserApiKey) {
  editingId.value = key.id
  editLabel.value = key.label
  editBaseUrl.value = key.base_url || ''
  editIsActive.value = key.is_active
  editKeyValue.value = ''
}

function cancelEdit() {
  editingId.value = null
  isEditing.value = false
}

async function handleEditSubmit() {
  if (!editingId.value || !editLabel.value.trim()) return
  isEditing.value = true
  try {
    const body: UpdateApiKeyPayload = { label: editLabel.value.trim() }
    const key = keys.value.find((k) => k.id === editingId.value)
    if (key?.provider === 'custom') {
      body.base_url = editBaseUrl.value
    }
    body.is_active = editIsActive.value
    if (editKeyValue.value.trim()) {
      body.key = editKeyValue.value.trim()
    }
    const updated = await updateKey(editingId.value, body)
    const idx = keys.value.findIndex((k) => k.id === editingId.value)
    if (idx !== -1) keys.value[idx] = updated
    editingId.value = null
    toast.add({ title: 'Key updated', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to update key', color: 'error' })
  } finally {
    isEditing.value = false
  }
}

// === Delete / Test ===

async function handleDelete(id: string) {
  deletingId.value = id
  try {
    await deleteKey(id)
    keys.value = keys.value.filter((k) => k.id !== id)
    toast.add({ title: 'API key deleted', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to delete key', color: 'error' })
  } finally {
    deletingId.value = null
  }
}

async function handleTest(id: string) {
  testingId.value = id
  try {
    const result = await testKey(id)
    toast.add({
      title: result.status === 'ok' ? 'Key works!' : 'Key test failed',
      description: result.detail,
      color: result.status === 'ok' ? 'success' : 'error',
    })
  } catch (err) {
    if (err instanceof SessionExpiredError) {
      getSessionKey().handleSessionExpired(() => handleTest(id))
      return
    }
    toast.add({ title: 'Key test failed', description: 'Could not connect', color: 'error' })
  } finally {
    testingId.value = null
  }
  try {
    keys.value = await fetchKeys()
  } catch {
    /* */
  }
  if (editingId.value === id) {
    const updated = keys.value.find((k) => k.id === id)
    if (updated) {
      editIsActive.value = updated.is_active
    }
  }
}
</script>

<template>
  <UModal v-model:open="open" title="Settings" :dismissible="true" class="max-w-2xl w-full">
    <template #body>
      <div>
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold">API Keys</h3>
          <UButton v-if="!showAddForm" size="sm" icon="i-lucide-plus" @click="showAddForm = true">
            Add Key
          </UButton>
        </div>

        <!-- Empty -->
        <div v-if="keys.length === 0 && !showAddForm" class="text-center py-8">
          <UIcon name="i-lucide-key-round" class="size-10 text-dimmed mx-auto mb-3" />
          <p class="text-sm text-dimmed mb-3">No API keys yet. Add one to use AI features.</p>
          <UButton @click="showAddForm = true">Add Your First Key</UButton>
        </div>

        <!-- Inline Add Form -->
        <div v-if="showAddForm" class="mb-4 p-4 border rounded-lg">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium">
              {{ formStep === 'provider' ? 'Select Provider' : 'Key Details' }}
            </h4>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              size="xs"
              @click="resetForm"
            />
          </div>

          <div v-if="formStep === 'provider'" class="space-y-3">
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="opt in PROVIDER_OPTIONS"
                :key="opt.value"
                class="relative p-3 rounded-lg border cursor-pointer hover:border-primary transition-colors text-center"
                :class="
                  formProvider === opt.value ? 'border-primary bg-primary/5' : 'border-default'
                "
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
                    @click.stop="showMorpheusHelp = true"
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
                @click="showMorpheusHelp = true"
                >how can i get a free api key?</UButton
              >
            </div>
            <template v-if="isCustom">
              <UInput v-model="formBaseUrl" placeholder="https://api.openai.com/v1" size="sm" />
              <p class="text-xs text-dimmed -mt-1">
                API base URL (e.g. https://opencode.ai/zen/go/v1 — <b>not</b> the /chat/completions
                path)
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

        <!-- Key List -->
        <div v-if="keys.length > 0" class="space-y-2">
          <div
            v-for="apiKey in keys"
            :key="apiKey.id"
            :class="[
              'p-3 border rounded-lg',
              apiKey.disabled_reason === 'auth_failure'
                ? 'border-red-500 bg-red-50 dark:bg-red-950/20'
                : '',
            ]"
          >
            <!-- Normal view -->
            <div v-if="editingId !== apiKey.id" class="flex items-center justify-between">
              <div class="flex items-center gap-3 min-w-0">
                <UIcon :name="PROVIDER_ICONS[apiKey.provider]" class="size-5 shrink-0" />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm truncate">{{ apiKey.label }}</span>
                    <UBadge
                      :color="
                        apiKey.disabled_reason === 'auth_failure'
                          ? 'error'
                          : apiKey.is_active
                            ? 'success'
                            : 'neutral'
                      "
                      variant="subtle"
                      size="xs"
                    >
                      {{
                        apiKey.disabled_reason === 'auth_failure'
                          ? 'Invalid'
                          : apiKey.is_active
                            ? 'Active'
                            : 'Off'
                      }}
                    </UBadge>
                  </div>
                  <div class="text-xs text-dimmed truncate">
                    {{ apiKey.masked_key }} · {{ PROVIDER_LABELS[apiKey.provider] }}
                    <span v-if="apiKey.base_url" class="ml-1 text-dimmed/70"
                      >· {{ apiKey.base_url }}</span
                    >
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-1 shrink-0">
                <UButton
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-pencil"
                  size="xs"
                  @click="startEdit(apiKey)"
                />
                <UButton
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-plug"
                  size="sm"
                  :loading="testingId === apiKey.id"
                  @click="handleTest(apiKey.id)"
                />
                <UButton
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="sm"
                  :loading="deletingId === apiKey.id"
                  @click="handleDelete(apiKey.id)"
                />
              </div>
            </div>

            <!-- Edit view -->
            <div v-else class="space-y-3">
              <div class="flex items-center justify-between">
                <h4 class="text-sm font-medium">Edit Key</h4>
                <UButton
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-x"
                  size="xs"
                  @click="cancelEdit"
                />
              </div>
              <UInput v-model="editLabel" placeholder="Label" size="sm" />
              <template
                v-if="
                  editingId &&
                  keys.find((k) => k.id === editingId)?.disabled_reason === 'auth_failure'
                "
              >
                <UInput
                  v-model="editKeyValue"
                  type="password"
                  placeholder="Enter new API key to replace the broken one"
                  size="sm"
                />
                <p class="text-xs text-amber-600 dark:text-amber-400 -mt-2">
                  This key was auto-disabled because the provider rejected it. Enter a new valid key
                  to re-enable it.
                </p>
              </template>
              <template v-if="isEditCustom">
                <UInput v-model="editBaseUrl" placeholder="https://api.openai.com/v1" size="sm" />
                <p class="text-xs text-dimmed -mt-2">
                  API base URL (the /v1 root, not /chat/completions)
                </p>
              </template>
              <div class="flex items-center gap-2">
                <label class="text-sm">Active:</label>
                <UButton
                  size="xs"
                  :color="editIsActive ? 'success' : 'neutral'"
                  variant="outline"
                  :disabled="
                    editingId
                      ? keys.find((k) => k.id === editingId)?.disabled_reason === 'auth_failure'
                      : false
                  "
                  @click="editIsActive = !editIsActive"
                >
                  {{ editIsActive ? 'Enabled' : 'Disabled' }}
                </UButton>
                <span
                  v-if="
                    editingId &&
                    keys.find((k) => k.id === editingId)?.disabled_reason === 'auth_failure'
                  "
                  class="text-xs text-amber-600 dark:text-amber-400"
                >
                  Must enter a new key to re-enable
                </span>
              </div>
              <div class="flex justify-end gap-2">
                <UButton
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-plug"
                  size="sm"
                  :loading="testingId === editingId"
                  @click="editingId ? handleTest(editingId) : undefined"
                />
                <UButton variant="ghost" size="sm" @click="cancelEdit">Cancel</UButton>
                <UButton size="sm" :loading="isEditing" @click="handleEditSubmit">Save</UButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </UModal>

  <!-- Morpheus Help Modal -->
  <UModal
    v-model:open="showMorpheusHelp"
    title="Morpheus (TUM CIT) — API Key Guide"
    class="max-w-lg w-full"
  >
    <template #body>
      <div class="space-y-4 text-sm">
        <p>
          <a href="https://morpheus.cit.tum.de" target="_blank" class="text-primary underline"
            >Morpheus</a
          >
          is the TUM CIT LLM cluster. It provides free, privacy-respecting access to open-source
          LLMs for students and staff.
        </p>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 1: Log in to Morpheus</p>
          <p>
            Go to
            <a href="https://morpheus.cit.tum.de" target="_blank" class="text-primary underline"
              >morpheus.cit.tum.de</a
            >
            and log in with your <b>CIT / RBG account</b> (the same credentials you use for CIT
            computer pools and other TUM CIT services).
          </p>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 2: Find your API Key</p>
          <p>Once logged in:</p>
          <ul class="list-disc pl-5 space-y-1">
            <li>Click on your <b>avatar / profile icon</b> (top-right corner).</li>
            <li>Go to <b>Settings</b> → <b>Account</b>.</li>
            <li>Scroll down to the <b>API Keys</b> section.</li>
            <li>Click <b>"Create API Key"</b> (or copy the existing one).</li>
            <li>
              Copy the key — it starts with <code class="text-xs bg-muted px-1 rounded">sk-</code>.
            </li>
          </ul>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Step 3: Add the key to pix:e</p>
          <p>Paste the key into the API Key field above.</p>
          <p class="text-dimmed text-xs">
            The base URL (<code class="text-xs bg-muted px-1 rounded"
              >https://morpheus.cit.tum.de/api</code
            >) is automatically configured — you don't need to enter it.
          </p>
        </div>

        <div class="bg-muted p-3 rounded-lg space-y-1">
          <p class="font-semibold">Available Models</p>
          <p>
            pix:e will automatically discover the available models from the Morpheus API. The
            currently supported models include:
          </p>
          <ul class="list-disc pl-5 space-y-0.5 text-xs">
            <li><b>ministral-3</b> — 14B params, 32K context (lightweight, European)</li>
            <li><b>gemma-4</b> — 31B params, 64K context (vision, thinking, coding)</li>
            <li><b>qwen-35-35b</b> — 35B params (general tasks)</li>
            <li><b>qwen-35-35b-coding</b> — 35B params (coding-optimised)</li>
          </ul>
        </div>

        <p class="text-xs text-dimmed">
          For questions or support:
          <a href="mailto:support@ito.cit.tum.de" class="text-primary underline"
            >support@ito.cit.tum.de</a
          >
        </p>
      </div>
    </template>
  </UModal>
</template>
