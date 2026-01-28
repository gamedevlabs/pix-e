<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const id = route.params.id as string

async function handleDelete() {
  await navigateTo('/pxnodes')
}
</script>

<template>
  <div class="p-8">
    <div>
      <PxNodeCard :node-id="id" :visualization-style="'detailed'" @delete="handleDelete" />
    </div>
    <UButton to="/pxnodes" class="my-4">← Back to all Nodes</UButton>
  </div>
</template>

<style scoped></style>
