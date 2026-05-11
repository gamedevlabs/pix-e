<script setup lang="ts">
import type { FormError, SelectMenuItem } from '@nuxt/ui'

definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    showInNav: false,
  },
})

const {
  items: pxLockDefinitions,
  fetchAll: fetchPxLockDefinitions,
  createItem: createPxLockDefinition,
  updateItem: updatePxLockDefinition,
  deleteItem: deletePxLockDefinition,
} = usePxLockDefinitions()

const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

onMounted(() => {
  fetchPxLockDefinitions()
  fetchPxKeyDefinitions()
})

const unlockModes = ref(['permanent', 'temporary', 'reversible', 'collapsible'])

export type PxKeySelectMenuItem = SelectMenuItem & { label: string; value: string }

const keysForSelection: Ref<PxKeySelectMenuItem[]> = computed(() => {
  return pxKeyDefinitions.value.map((def) => ({ label: def.name, value: def.id }))
})

interface PxLockDefState {
  name: string
  soft_gate: boolean
  unlocked_by: string[]
  unlock_mode: PxLockUnlockModeType
}

const defaultState: PxLockDefState = {
  name: '',
  soft_gate: false,
  unlocked_by: [],
  unlock_mode: 'permanent',
}

const state = ref<PxLockDefState>(defaultState)

function validate(state: Partial<PxLockDefState>): FormError[] {
  const errors = []
  if (!state.name) errors.push({ name: 'name', message: 'Required' })
  if (!state.unlocked_by?.length) errors.push({ name: 'unlocked_by', message: 'Required' })
  return errors
}

async function handleCreate() {
  await createPxLockDefinition({ ...state.value })
  state.value = defaultState
}

async function handleUpdate(updatedDefinition: PxLockDefinition) {
  await updatePxLockDefinition(updatedDefinition.id, updatedDefinition)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">PxLock Definitions</h1>

    <UForm :state="state" class="mb-6 space-y-4" :validate="validate" @submit="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>
      <UFormField label="Soft Gate?">
        <UCheckbox v-model="state.soft_gate" />
      </UFormField>
      <UFormField label="Unlock Mode">
        <USelectMenu v-model="state.unlock_mode" :items="unlockModes" />
      </UFormField>
      <UFormField label="Unlocked By">
        <USelectMenu
          v-model="state.unlocked_by"
          :items="keysForSelection"
          :value-key="'value'"
          multiple
        />
      </UFormField>
      <UButton type="submit">Create Lock</UButton>
    </UForm>

    <div>
      <SimpleContentWrapper>
        <SimpleCardSection>
          <div v-for="definition in pxLockDefinitions" :key="definition.id">
            <PxLockDefinitionCardDetailed
              :definition="definition"
              :keys-for-selection="keysForSelection"
              @edit="handleUpdate"
              @delete="deletePxLockDefinition"
            />
          </div>
        </SimpleCardSection>
      </SimpleContentWrapper>
    </div>
  </div>
</template>

<style scoped></style>
