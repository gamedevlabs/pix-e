<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const route = useRoute()
const id = route.params.id as unknown as number

const {
  fetchById: fetchPxNodeById,
  updateItem: updatePxNode,
  deleteItem: deletePxNode,
  loading: loadingPxNode,
  error: errorPxNode,
} = usePxNodes()

const fetchedNode = ref<PxNode | null>(null)

onMounted(() => {
  getNode()
})

async function getNode() {
  fetchedNode.value = await fetchPxNodeById(id)
}

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)

  fetchedNode.value = updatedNode
}

async function handleDelete() {
  await deletePxNode(id)

  await navigateTo('/pxnodes')
}
</script>

<template>
  <div class="p-8">
    <div v-if="errorPxNode">
      <div v-if="errorPxNode.response?.status === 403">You do not have access to this node.</div>
      <div v-if="errorPxNode.response?.status === 404">This node does not exist.</div>
    </div>
    <div v-else-if="fetchedNode">
      <PxNodeCard
        :node="fetchedNode"
        visualization-style="detailed"
        @edit="handleUpdate"
        @delete="handleDelete"
      />
    </div>
    <div v-else-if="loadingPxNode">Loading...</div>
    <UButton to="/pxnodes" class="my-4">← Back to all Nodes</UButton>
  </div>
</template>

<style scoped></style>
