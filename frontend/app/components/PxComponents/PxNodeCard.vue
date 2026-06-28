<script setup lang="ts">
import PxNodeCardSimple from '~/components/PxComponents/PxNodeCardSimple.vue'

const props = defineProps({
  nodeId: {
    type: String as PropType<string>,
    required: true,
  },
  visualizationStyle: {
    type: String as PropType<'preview' | 'detailed' | 'simple'>,
    default: 'detailed',
  },
  showContextMenu: {
    type: Boolean,
    default: false,
  },
  isCollapsible: {
    type: Boolean,
    default: false,
  },
})

const {
  error: nodeError,
  loading: nodeLoading,
  fetchById: fetchNodeById,
  updateItem: updatePxNode,
} = usePxNodes()

const { toggleSubstep } = useProjectWorkflow()
const { fetchById: fetchComponentById } = usePxComponents()
const { fetchById: fetchPxKeyById } = usePxKeys()

// TODO: figure out what "addForeign" is supposed to do and clean up emits
const emit = defineEmits<{
  (e: 'addForeignComponent' | 'addForeignKey', nodeId: string, componentId: string): void
  (e: 'addComponent' | 'addKey' | 'deleteKey' | 'componentsUpdated'): void
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
  // px-2-2: "Add a component to your new node"
  console.log('addedComp')
  await toggleSubstep('px-2', 'px-2-2')
  fetchedNode.value.components.push(addedComponent!)

  emit('componentsUpdated')
}

async function handleDeleteComponent(nodeId: string, componentId: string) {
  const index = fetchedNode.value.components.findIndex((component) => component.id === componentId)
  if (index > -1) {
    fetchedNode.value.components.splice(index, 1)
  }

  emit('componentsUpdated')
}

async function handleAddKey(nodeId: string, keyId: string) {
  if (nodeId !== fetchedNode.value.id) {
    emit('addForeignComponent', nodeId, keyId)
    return
  }

  let addedKey
  try {
    addedKey = await fetchPxKeyById(keyId)
  } catch (err) {
    console.error(err)
  }
  fetchedNode.value.keys.push(addedKey!)
  emit('addKey')
}

async function handleDeleteKey(nodeId: string, keyId: string) {
  const index = fetchedNode.value.keys.findIndex((key) => key.id === keyId)
  if (index > -1) {
    fetchedNode.value.keys.splice(index, 1)
    emit('deleteKey')
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
    :is-collapsible="isCollapsible"
    @delete-component="handleDeleteComponent"
    @add-component="handleAddComponent"
    @delete-key="handleDeleteKey"
    @add-key="handleAddKey"
    @update="handleUpdate"
  />
  <PxNodeCardSimple
    v-else-if="fetchedNode?.components && visualizationStyle === 'simple'"
    :node="fetchedNode"
    :is-collapsible="isCollapsible"
    :show-context-menu="showContextMenu"
    @delete-component="handleDeleteComponent"
    @add-component="handleAddComponent"
    @delete-key="handleDeleteKey"
    @add-key="handleAddKey"
    @update="handleUpdate"
  >
    <template #bottom-right-buttons>
      <slot name="bottom-right-buttons" />
    </template>
  </PxNodeCardSimple>
</template>

<style scoped></style>
