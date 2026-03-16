<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'PxKey Definitions',
    icon: 'i-lucide-key',
    navGroup: 'main',
    navParent: 'pxlockkeydefinitions',
    navOrder: 2,
    showInNav: true,
  },
})

const {
  items: pxKeyDefinitions,
  fetchAll: fetchPxKeyDefinitions,
  createItem: createPxKeyDefinition,
  updateItem: updatePxKeyDefinition,
  deleteItem: deletePxKeyDefinition,
} = usePxKeyDefinitions()

onMounted(() => {
  fetchPxKeyDefinitions()
})

const items = ref(['item', 'ability'])

interface KeyState {
  name: string
  type: PxKeyTypesType
  consumable: boolean
  fixed: boolean
  unique: boolean
}

const defaultState: KeyState = {
  name: '',
  type: 'none',
  consumable: false,
  fixed: false,
  unique: false,
}

const state = ref<KeyState>(defaultState)

async function handleCreate() {
  await createPxKeyDefinition({ ...state.value })
  state.value = defaultState
}

async function handleUpdate(updatedDefinition: PxKeyDefinition) {
  await updatePxKeyDefinition(updatedDefinition.id, updatedDefinition)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">PxKey Definitions</h1>

    <UForm :state="state" class="mb-6 space-y-4" @submit="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>
      <UFormField label="Type" name="type">
        <USelectMenu v-model="state.type" :items="items" />
      </UFormField>
      <UCheckbox v-model="state.consumable" label="Consumable" description="This is a checkbox." />
      <UCheckbox v-model="state.fixed" label="Fixed" description="This is a checkbox." />
      <UCheckbox v-model="state.unique" label="Unique" description="This is a checkbox." />
      <UButton type="submit">Create Key</UButton>
    </UForm>

    <div>
      <SimpleContentWrapper>
        <SimpleCardSection>
          <div v-for="definition in pxKeyDefinitions" :key="definition.id">
            <PxKeyDefinitionCardDetailed
              :definition="definition"
              @edit="handleUpdate"
              @delete="deletePxKeyDefinition"
            />
          </div>
        </SimpleCardSection>
      </SimpleContentWrapper>
    </div>
  </div>
</template>

<style scoped></style>
