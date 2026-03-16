<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const id = route.params.id as string

const {
  fetchById: fetchPxLockDefinition,
  updateItem: updatePxLockDefinition,
  deleteItem: deletePxLockDefinition,
  loading: loadingPxLockDefinition,
  error: errorPxLockDefinition,
} = usePxLockDefinitions()

const fetchedDefinition = ref<PxLockDefinition | null>(null)

onMounted(() => {
  getDefinition()
})

async function getDefinition() {
  fetchedDefinition.value = await fetchPxLockDefinition(id)
}

async function handleUpdate(updatedDefinition: PxLockDefinition) {
  await updatePxLockDefinition(updatedDefinition.id, updatedDefinition)

  fetchedDefinition.value = updatedDefinition
}

async function handleDelete() {
  await deletePxLockDefinition(id)

  await navigateTo('/pxlockkeydefinitions')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxLockDefinition">Error loading definition.</div>
    <div v-else-if="fetchedDefinition">
      <PxLockDefinitionCard
        visualization-style="detailed"
        :definition="fetchedDefinition"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-if="loadingPxLockDefinition">Loading Px Lock Definition {{ id }}</div>
    <div>
      <UButton to="/pxlockkeydefinitions" class="my-4">← Back to all definitions</UButton>
    </div>
  </div>
</template>

<style scoped></style>
