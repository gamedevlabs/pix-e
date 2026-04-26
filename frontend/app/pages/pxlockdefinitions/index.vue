<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'PxLock Definitions',
    icon: 'i-lucide-lock',
    navGroup: 'main',
    navParent: 'pxlockkeydefinitions',
    navOrder: 1,
    showInNav: true,
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

const keys = computed(() => {
  return pxKeyDefinitions.value.map((def) => def.name)
})

interface LockState {
  name: string
  softGate: boolean
  unlockedBy: string[]
  unlockMode: PxLockUnlockModeType
}

const defaultState: LockState = {
  name: '',
  softGate: false,
  unlockedBy: [],
  unlockMode: 'permanent',
}

const state = ref<LockState>(defaultState)

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

    <UForm :state="state" class="mb-6 space-y-4" @submit="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>
      <UFormField label="Soft Gate?">
        <UCheckbox v-model="state.softGate" />
      </UFormField>
      <UFormField label="Unlock Mode">
        <USelectMenu v-model="state.unlockMode" :items="unlockModes" />
      </UFormField>
      <UFormField label="Unlocked By">
        <USelectMenu v-model="state.unlockedBy" :items="keys" multiple />
      </UFormField>
      <UButton type="submit">Create Lock</UButton>
    </UForm>

    <div>
      <SimpleContentWrapper>
        <SimpleCardSection>
          <div v-for="definition in pxLockDefinitions" :key="definition.id">
            <PxLockDefinitionCardDetailed
              :definition="definition"
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
