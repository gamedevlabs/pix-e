<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const { data: node, status, error } = await useFetch<PxNode>(`http://localhost:8000/pxnodes/${id}/`)
</script>

<template>
  <div class="p-8">
    <div v-if="status==='pending'">Loading...</div>
    <div v-else-if="error">Error loading node.</div>
    <div v-else>
      <h1 class="text-2xl font-bold mb-4">{{ node?.name }}</h1>
      <p class="text-gray-600 mb-6">{{ node?.description }}</p>
      <NuxtLink to="/pxnodes" class="text-blue-500 underline">← Back to Nodes</NuxtLink>
    </div>
  </div>
</template>

<style scoped>

</style>