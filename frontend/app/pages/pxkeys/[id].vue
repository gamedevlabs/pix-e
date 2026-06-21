<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const id = route.params.id as string

const {
  fetchById: fetchPxKeyById,
  updateItem: updatePxKey,
  loading: loadingPxKey,
  error: errorPxKey,
} = usePxKeys()

const fetchedKey = ref<PxKey | null>(null)

onMounted(() => {
  getKey()
})

async function getKey() {
  fetchedKey.value = await fetchPxKeyById(id)
}

async function handleUpdate(updatedKey: PxKey) {
  await updatePxKey(updatedKey.id, updatedKey)

  fetchedKey.value = updatedKey
}

async function handleDelete() {
  await navigateTo('/pxkeys')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxKey">Error loading key.</div>
    <div v-else-if="fetchedKey">
      <PxKeyCard
        visualization-style="detailed"
        :pxkey="fetchedKey"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-else-if="loadingPxKey">Loading Px Key {{ id }}</div>
    <UButton to="/pxkeys" class="my-4">← Back to all Keys</UButton>
  </div>
</template>

<style scoped></style>
