<script setup lang="ts">
const props = defineProps<{
  pxkey: PxKey
  definition?: PxKeyDefinition
  node?: PxNode
  visualizationStyle: 'preview' | 'detailed'
}>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

const { deleteItem: deletePxKey } = usePxKeys()

const { fetchById: fetchPxDefinitionById } = usePxKeyDefinitions()

const { fetchById: fetchPxNodeById } = usePxNodes()

onMounted(() => {
  getDefinition()
  getEdge()
})

const associatedDefinition = ref<PxKeyDefinition | null>(null)
const associatedNode = ref<PxNode | null>(null)

async function getDefinition() {
  if (props.definition) {
    associatedDefinition.value = props.definition
    return
  }
  associatedDefinition.value = await fetchPxDefinitionById(props.pxkey.definition)
}

async function getEdge() {
  if (props.node) {
    associatedNode.value = props.node
    return
  }
  associatedNode.value = await fetchPxNodeById(props.pxkey.node)
}

async function handleDelete(id: string) {
  await deletePxKey(id)

  emit('delete', id)
}
</script>

<template>
  <div v-if="!associatedNode || !associatedDefinition">Loading PxKey {{ pxkey.id }}</div>
  <PxKeyCardPreview
    v-else-if="visualizationStyle === 'preview'"
    :pxkey="pxkey"
    :definition="associatedDefinition!"
    @delete="handleDelete"
  />

  <PxKeyCardDetailed
    v-else
    :pxkey="pxkey"
    :definition="associatedDefinition!"
    :node="associatedNode!"
    @delete="handleDelete"
  />
</template>
<style scoped></style>
