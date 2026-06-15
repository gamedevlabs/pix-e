<script setup lang="ts">
import type { UserApiKey } from '~/types/api-key'
import { SessionExpiredError } from '~/utils/sessionFetch'
import { getSessionKey } from '~/composables/useSessionKey'
import { useApiKeysApi } from '~/composables/api/apiKeysApi'
import ApiKeyAddForm from '~/components/ApiKeyAddForm.vue'
import ApiKeyList from '~/components/ApiKeyList.vue'
import MorpheusHelpModal from '~/components/MorpheusHelpModal.vue'

const open = defineModel<boolean>('open', { default: false })

///////////////new
const props = withDefaults(defineProps<{ presetProvider?: string }>(), { presetProvider: '' })
const llmStore = useLLM()

const { fetchKeys, testKey } = useApiKeysApi()
const keys = ref<UserApiKey[]>([])
const toast = useToast()

const showAddForm = ref(false)
const showMorpheusHelp = ref(false)
const testingId = ref<string | null>(null)

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
  } else {
    showAddForm.value = false
  }

  //////////newwwwww
  // If presetProvider was given, jump directly to the add-form with provider pre-selected
  if (props.presetProvider) {
    showAddForm.value = true
    formStep.value = 'details'
    formProvider.value = props.presetProvider
    formLabel.value = `${props.presetProvider.charAt(0).toUpperCase() + props.presetProvider.slice(1)} Key`
  }
  /////////////////



})

async function onKeyCreated(key: UserApiKey) {
  keys.value.push(key)
  showAddForm.value = false
  try {
    await llmStore.refreshModels()
  } catch {
    getSessionKey().handleSessionExpired(() => llmStore.refreshModels())
  }
}

function onKeyUpdated(updated: UserApiKey) {
  const idx = keys.value.findIndex((k) => k.id === updated.id)
  if (idx !== -1) keys.value[idx] = updated
}

async function onKeyDeleted(id: string) {
  keys.value = keys.value.filter((k) => k.id !== id)
  // Optimistic: remove models from this key immediately
  if (llmStore.models) {
    llmStore.models = llmStore.models.filter((m) => m.apiKeyId !== id)
  }
  try {
    await llmStore.refreshModels()
  } catch {
    getSessionKey().handleSessionExpired(() => llmStore.refreshModels())
  }
}

async function onKeyTest(id: string) {
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
      getSessionKey().handleSessionExpired(() => onKeyTest(id))
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

        <ApiKeyAddForm
          v-if="showAddForm"
          @close="showAddForm = false"
          @created="onKeyCreated"
          @show-morpheus-help="showMorpheusHelp = true"
        />

        <div v-if="keys.length === 0 && !showAddForm" class="text-center py-8">
          <UIcon name="i-lucide-key-round" class="size-10 text-dimmed mx-auto mb-3" />
          <p class="text-sm text-dimmed mb-3">No API keys yet. Add one to use AI features.</p>
          <UButton @click="showAddForm = true">Add Your First Key</UButton>
        </div>

        <ApiKeyList
          v-if="keys.length > 0"
          :keys="keys"
          :testing-id="testingId"
          @updated="onKeyUpdated"
          @deleted="onKeyDeleted"
          @test="onKeyTest"
        />
      </div>
    </template>
  </UModal>

  <MorpheusHelpModal v-model:open="showMorpheusHelp" />
</template>
