<script setup lang="ts">
const route = useRoute()
const id = route.params.id as string

const { data: node, status, error } = await useFetch<PxNode>(`http://localhost:8000/pxnodes/${id}/`)

const { updateItem: updatePxNode, deleteItem: deletePxNode } = usePxNodes()

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)
}

async function handleAddComponent() {
  console.log('AddComponent')
}
</script>

<template>
  <div class="p-8">
    <div v-if="status === 'pending'">Loading...</div>
    <div v-else-if="error">Error loading node.</div>
    <div v-else-if="node">
      <PxNodeCard
        :node="node"
        @add-component="handleAddComponent"
        @edit="handleUpdate"
        @delete="deletePxNode"
      />
    </div>
    <UButton to="/pxnodes" class="my-4">← Back to all Nodes</UButton>
  </div>
</template>

<style scoped></style>
