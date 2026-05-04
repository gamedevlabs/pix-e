<script setup lang="ts">
import type { FormError } from '@nuxt/ui'

definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Component Definitions',
    icon: 'i-lucide-library-big',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 3,
    showInNav: true,
  },
})

const {
  items: pxComponentDefinitions,
  fetchAll: fetchPxComponentDefinitions,
  createItem: createPxComponentDefinition,
  updateItem: updatePxDefinition,
  deleteItem: deletePxDefinition,
} = usePxComponentDefinitions()

onMounted(() => {
  fetchPxComponentDefinitions()
})

const items = ref(['number', 'string', 'boolean'])

interface PxDefState {
  name: string
  type: PxValueType | undefined
}

const state = ref<PxDefState>({
  name: '',
  type: undefined,
})

const { currentProject } = useProjectHandler()
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

function validate(state: PxDefState): FormError[] {
  const errors = []
  if (!state.name) errors.push({ name: 'name', message: 'Required' })
  if (!state.type) errors.push({ name: 'type', message: 'Required' })
  return errors
}

async function handleCreate() {
  await createPxComponentDefinition({ ...state.value })
  // px-2-1: "Add a Component Definition"
  await toggleSubstep('px-2', 'px-2-1')
  state.value.name = ''
  state.value.type = 'none'
}

async function handleUpdate(updatedDefinition: PxComponentDefinition) {
  await updatePxDefinition(updatedDefinition.id, updatedDefinition)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Component Definitions</h1>

    <UForm :state="state" class="mb-6 space-y-4" :validate="validate" @submit="handleCreate">
      <UFormField name="name">
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>
      <UFormField label="Type" name="type">
        <USelectMenu v-model="state.type" :items="items" placeholder="Select Type" />
      </UFormField>
      <UButton type="submit">Create Component</UButton>
    </UForm>

    <div>
      <SimpleContentWrapper>
        <SimpleCardSection>
          <div v-for="definition in pxComponentDefinitions" :key="definition.id">
            <PxComponentDefinitionCardDetailed
              :definition="definition"
              @edit="handleUpdate"
              @delete="deletePxDefinition"
            />
          </div>
        </SimpleCardSection>
      </SimpleContentWrapper>
    </div>
  </div>
</template>

<style scoped></style>
