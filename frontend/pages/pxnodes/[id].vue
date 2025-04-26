<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const { data: node, status, error } = await useFetch<PxNode>(`http://localhost:8000/pxnodes/${id}/`)
</script>

<template>
  <div class="p-8">
    <div v-if="status === 'pending'">Loading...</div>
    <div v-else-if="error">Error loading node.</div>
    <div v-else-if="node">
      <PxNodeCard v-if="node" :node="node" />
      <UButton to="/pxnodes" class="my-4">← Back to Nodes</UButton>
    </div>
  </div>
</template>

<style scoped></style>
