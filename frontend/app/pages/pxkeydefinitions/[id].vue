<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const id = route.params.id as string

const {
  fetchById: fetchPxKeyDefinition,
  updateItem: updatePxKeyDefinition,
  deleteItem: deletePxKeyDefinition,
  loading: loadingPxKeyDefinition,
  error: errorPxKeyDefinition,
} = usePxKeyDefinitions()

const fetchedDefinition = ref<PxKeyDefinition | null>(null)

onMounted(() => {
  getDefinition()
})

async function getDefinition() {
  fetchedDefinition.value = await fetchPxKeyDefinition(id)
}

async function handleUpdate(updatedDefinition: PxKeyDefinition) {
  await updatePxKeyDefinition(updatedDefinition.id, updatedDefinition)

  fetchedDefinition.value = updatedDefinition
}

async function handleDelete() {
  await deletePxKeyDefinition(id)

  await navigateTo('/pxlockkeydefinitions')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxKeyDefinition">Error loading definition.</div>
    <div v-else-if="fetchedDefinition">
      <PxKeyDefinitionCard
        visualization-style="detailed"
        :definition="fetchedDefinition"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-if="loadingPxKeyDefinition">Loading Px Key Definition {{ id }}</div>
    <div>
      <UButton to="/pxlockkeydefinitions" class="my-4">← Back to all definitions</UButton>
    </div>
  </div>
</template>

<style scoped></style>
