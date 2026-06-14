<script setup lang="ts">
import type { UpdateApiKeyPayload, UserApiKey } from '~/types/api-key'
import { PROVIDER_ICONS, PROVIDER_LABELS } from '~/utils/api-key'
import { useApiKeysApi } from '~/composables/api/apiKeysApi'

const props = defineProps<{
  keys: UserApiKey[]
}>()

const emit = defineEmits<{
  updated: [key: UserApiKey]
  deleted: [id: string]
}>()

const { updateKey, deleteKey } = useApiKeysApi()
const toast = useToast()

const editingId = ref<string | null>(null)
const editLabel = ref('')
const editBaseUrl = ref('')
const editIsActive = ref(true)
const editKeyValue = ref('')
const isEditing = ref(false)
const deletingId = ref<string | null>(null)

const isEditCustom = computed(() => {
  const key = props.keys.find((k) => k.id === editingId.value)
  return key?.provider === 'custom'
})

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
    const key = props.keys.find((k) => k.id === editingId.value)
    if (key?.provider === 'custom') {
      body.base_url = editBaseUrl.value
    }
    body.is_active = editIsActive.value
    if (editKeyValue.value.trim()) {
      body.key = editKeyValue.value.trim()
    }
    const updated = await updateKey(editingId.value, body)
    emit('updated', updated)
    editingId.value = null
    toast.add({ title: 'Key updated', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to update key', color: 'error' })
  } finally {
    isEditing.value = false
  }
}

async function handleDelete(id: string) {
  deletingId.value = id
  try {
    await deleteKey(id)
    emit('deleted', id)
    toast.add({ title: 'API key deleted', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to delete key', color: 'error' })
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <div class="space-y-2">
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
            color="error"
            icon="i-lucide-trash-2"
            size="sm"
            :loading="deletingId === apiKey.id"
            @click="handleDelete(apiKey.id)"
          />
        </div>
      </div>

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
            editingId && keys.find((k) => k.id === editingId)?.disabled_reason === 'auth_failure'
          "
        >
          <UInput
            v-model="editKeyValue"
            type="password"
            placeholder="Enter new API key to replace the broken one"
            size="sm"
          />
          <p class="text-xs text-amber-600 dark:text-amber-400 -mt-2">
            This key was auto-disabled because the provider rejected it. Enter a new valid key to
            re-enable it.
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
              editingId && keys.find((k) => k.id === editingId)?.disabled_reason === 'auth_failure'
            "
            class="text-xs text-amber-600 dark:text-amber-400"
          >
            Must enter a new key to re-enable
          </span>
        </div>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" size="sm" @click="cancelEdit">Cancel</UButton>
          <UButton size="sm" :loading="isEditing" @click="handleEditSubmit">Save</UButton>
        </div>
      </div>
    </div>
  </div>
</template>
