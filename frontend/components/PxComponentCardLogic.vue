<script setup lang="ts">
const props = defineProps<{
  component: PxComponent
  definition?: PxComponentDefinition
  node?: PxNode
  visualizationStyle: 'preview' | 'detailed'
}>()

const emit = defineEmits<{
  (e: 'delete', id: number): void
}>()

const { deleteItem: deletePxComponent } = usePxComponents()

const { fetchById: fetchPxDefinitionById } = usePxComponentDefinitions()

const { fetchById: fetchPxNodeById } = usePxNodes()

onMounted(() => {
  getDefinition()
  getNode()
})

const associatedDefinition = ref<PxComponentDefinition | null>(null)
const associatedNode = ref<PxNode | null>(null)

async function getDefinition() {
  if (props.definition) {
    associatedDefinition.value = props.definition
    return
  }
  associatedDefinition.value = await fetchPxDefinitionById(props.component.definition)
}

async function getNode() {
  if (props.node) {
    associatedNode.value = props.node
    return
  }
  associatedNode.value = await fetchPxNodeById(props.component.node)
}

async function handleDelete(id: number) {
  await deletePxComponent(id)

  emit('delete', id)
}
</script>

<template>
  <div v-if="!associatedNode || !associatedDefinition">Loading...</div>
  <PxComponentCardPreview
    v-else-if="visualizationStyle === 'preview'"
    :component="component"
    :definition="associatedDefinition!"
    @delete="handleDelete"
  />

  <PxComponentCardDetailed
    v-else
    :component="component"
    :definition="associatedDefinition!"
    :node="associatedNode!"
    @delete="handleDelete"
  />
</template>
<style scoped></style>
