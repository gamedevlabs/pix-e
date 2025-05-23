<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const {
  data: component,
  status,
  error,
} = await useFetch<PxComponent>(`http://localhost:8000/pxcomponents/${id}/`)
</script>

<template>
  <div class="p-8">
    <div v-if="status === 'pending'">Loading...</div>
    <div v-else-if="error">Error loading node.</div>
    <div v-else-if="component">
      <PxComponentCard v-if="component" :component="component" />
    </div>
    <UButton to="/pxcomponents" class="my-4">← Back to all Components</UButton>
  </div>
</template>

<style scoped></style>
