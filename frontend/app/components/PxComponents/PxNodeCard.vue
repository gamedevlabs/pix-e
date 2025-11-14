<script setup lang="ts">
const props = defineProps({
  nodeId: {
    type: String as PropType<string>,
    required: true,
  },
  visualizationStyle: {
    type: String as PropType<'preview' | 'detailed'>,
    default: 'detailed',
  },
})

const {
  error: nodeError,
  loading: nodeLoading,
  fetchById: fetchNodeById,
  updateItem: updatePxNode,
} = usePxNodes()

const { fetchById: fetchComponentById } = usePxComponents()

const emit = defineEmits<{
  (e: 'addForeignComponent', nodeId: string, componentId: string): void
}>()

onMounted(() => {
  getNodeInformation()
})

const fetchedNode = ref<PxNode>(null)

async function getNodeInformation() {
  try {
    fetchedNode.value = await fetchNodeById(props.nodeId)
  } catch (err) {
    console.error(err)
  }
}

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)
  await getNodeInformation()
}

async function handleAddComponent(nodeId: string, componentId: string) {
  if (nodeId !== fetchedNode.value.id) {
    emit('addForeignComponent', nodeId, componentId)
    return
  }

  let addedComponent
  try {
    addedComponent = await fetchComponentById(componentId)
  } catch (err) {
    console.error(err)
  }
  fetchedNode.value.components.push(addedComponent!)
}

async function handleDeleteComponent(nodeId: string, componentId: string) {
  const index = fetchedNode.value.components.findIndex((component) => component.id === componentId)
  if (index > -1) {
    fetchedNode.value.components.splice(index, 1)
  }
}
</script>

<template>
  <div v-if="nodeError">
    <div v-if="nodeError.response?.status === 403">You do not have access to this node.</div>
    <div v-else-if="nodeError.response?.status === 404">This node does not exist.</div>
    <div v-else>Error loading Px Node {{ props.nodeId }}</div>
  </div>
  <div v-else-if="nodeLoading || !fetchedNode">Loading PxNode {{ props.nodeId }}</div>
  <PxNodeCardPreview v-else-if="visualizationStyle === 'preview'" :node="fetchedNode" />
  <PxNodeCardDetailed
    v-else-if="fetchedNode?.components && visualizationStyle === 'detailed'"
    :node="fetchedNode"
    @delete-component="handleDeleteComponent"
    @add-component="handleAddComponent"
    @update="handleUpdate"
  />
</template>

<style scoped></style>
