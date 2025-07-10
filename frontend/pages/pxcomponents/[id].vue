<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const {
  fetchById: fetchPxComponentById,
  updateItem: updatePxComponent,
  loading: loadingPxComponent,
  error: errorPxComponent,
} = usePxComponents()

const fetchedComponent = ref<PxComponent | null>(null)

onMounted(() => {
  getComponent()
})

async function getComponent() {
  fetchedComponent.value = await fetchPxComponentById(id)
}

async function handleUpdate(updatedComponent: PxComponent) {
  await updatePxComponent(updatedComponent.id, updatedComponent)

  fetchedComponent.value = updatedComponent
}

async function handleDelete() {
  await navigateTo('/pxcomponents')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxComponent">Error loading component.</div>
    <div v-else-if="fetchedComponent">
      <PxComponentCard
        visualization-style="detailed"
        :component="fetchedComponent"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-else-if="loadingPxComponent">Loading...</div>
    <UButton to="/pxcomponents" class="my-4">← Back to all Components</UButton>
  </div>
</template>

<style scoped></style>
