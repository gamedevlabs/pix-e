<script setup lang="ts">
const route = useRoute()
const id = route.params.id as unknown as number

const {
  fetchById: fetchPxDefinition,
  updateItem: updatePxDefinition,
  deleteItem: deletePxDefinition,
  loading: loadingPxDefinition,
  error: errorPxDefinition,
} = usePxComponentDefinitions()

const fetchedDefinition = ref<PxComponentDefinition | null>(null)

onMounted(() => {
  getDefinition()
})

async function getDefinition() {
  fetchedDefinition.value = await fetchPxDefinition(id)
}

async function handleUpdate(updatedDefinition: PxComponentDefinition) {
  await updatePxDefinition(updatedDefinition.id, updatedDefinition)

  fetchedDefinition.value = updatedDefinition
}

async function handleDelete() {
  await deletePxDefinition(id)

  await navigateTo('/pxcomponentdefinitions')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxDefinition">Error loading definition.</div>
    <div v-else-if="fetchedDefinition">
      <PxComponentDefinitionCardLogic
        visualization-style="detailed"
        :definition="fetchedDefinition"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-if="loadingPxDefinition">Loading...</div>
    <div>
      <UButton to="/pxcomponentdefinitions" class="my-4">← Back to all definitions</UButton>
    </div>
  </div>
</template>

<style scoped></style>
