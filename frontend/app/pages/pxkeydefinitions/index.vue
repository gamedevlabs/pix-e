<script setup lang="ts">
import type { FormError } from '@nuxt/ui'

definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    showInNav: false,
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

interface PxKeyDefState {
  name: string
  type: PxKeyTypesType | undefined
  consumable: boolean
  fixed: boolean
  unique: boolean
}

const defaultState: PxKeyDefState = {
  name: '',
  type: undefined,
  consumable: false,
  fixed: false,
  unique: false,
}

const state = ref<PxKeyDefState>(defaultState)

function validate(state: Partial<PxKeyDefState>): FormError[] {
  const errors = []
  if (!state.name) errors.push({ name: 'name', message: 'Required' })
  if (!state.type) errors.push({ name: 'type', message: 'Required' })
  return errors
}

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

    <UForm :state="state" class="mb-6 space-y-4" :validate="validate" @submit="handleCreate">
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
