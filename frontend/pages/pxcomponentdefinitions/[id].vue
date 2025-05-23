<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const {
  data: definition,
  status,
  error,
} = await useFetch<PxComponentDefinition>(`http://localhost:8000/pxcomponentdefinitions/${id}/`)
</script>

<template>
  <div class="p-8">
    <div v-if="status === 'pending'">Loading...</div>
    <div v-else-if="error">Error loading definition.</div>
    <div v-else-if="definition">
      <PxComponentDefinitionCard v-if="definition" :definition="definition" />
    </div>
    <div>
      <UButton to="/pxcomponentdefinitions" class="my-4">← Back to all definitions</UButton>
    </div>
  </div>
</template>

<style scoped></style>
