<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
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

const state = ref<{ name: string; type: PxValueType }>({
  name: '',
  type: 'none',
})

async function handleCreate() {
  await createPxComponentDefinition({ ...state.value })
  state.value.name = ''
  state.value.type = 'none'
}

async function handleUpdate(updatedDefinition: PxComponentDefinition) {
  await updatePxDefinition(updatedDefinition.id, updatedDefinition)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Px Definitions</h1>

    <UForm :state="state" class="mb-6 space-y-4" @submit="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>
      <UFormField label="Type" name="type">
        <USelectMenu v-model="state.type" :items="items" />
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
