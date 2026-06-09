<script setup lang="ts">
import type { UserApiKey } from '~/types/api-key'
import { useApiKeysApi } from '~/composables/api/apiKeysApi'
import ApiKeyAddForm from '~/components/ApiKeyAddForm.vue'
import ApiKeyList from '~/components/ApiKeyList.vue'
import MorpheusHelpModal from '~/components/MorpheusHelpModal.vue'

const open = defineModel<boolean>('open', { default: false })

const { fetchKeys } = useApiKeysApi()
const keys = ref<UserApiKey[]>([])

const showAddForm = ref(false)
const showMorpheusHelp = ref(false)

watch(open, async (val) => {
  if (val) {
    try {
      keys.value = await fetchKeys()
    } catch {
      /* */
    }
  } else {
    showAddForm.value = false
  }
})

function onKeyCreated(key: UserApiKey) {
  keys.value.push(key)
  showAddForm.value = false
}

function onKeyUpdated(updated: UserApiKey) {
  const idx = keys.value.findIndex((k) => k.id === updated.id)
  if (idx !== -1) keys.value[idx] = updated
}

function onKeyDeleted(id: string) {
  keys.value = keys.value.filter((k) => k.id !== id)
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
          @updated="onKeyUpdated"
          @deleted="onKeyDeleted"
        />
      </div>
    </template>
  </UModal>

  <MorpheusHelpModal v-model:open="showMorpheusHelp" />
</template>
