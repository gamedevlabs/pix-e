<script setup lang="ts">
const props = defineProps<{
  definition: PxComponentDefinition
  visualizationStyle: 'preview' | 'detailed'
}>()

const emit = defineEmits<{
  (e: 'edit', updatedDefinition: PxComponentDefinition): void
  (e: 'delete', id: number): void
}>()

function confirmEdit() {
  isBeingEdited.value = false
  emit('edit', { ...props.node, ...editForm.value })
}

function emitDelete() {
  emit('delete', props.definition.id)
}
</script>

<template>
  <PxComponentDefinitionCardPreview
    v-if="visualizationStyle === 'preview'"
    :definition="definition"
  />

  <PxComponentDefinitionCardDetailed
    v-else
    :definition="definition"
    :visualization-style="'detailed'"
    @edit="confirmEdit"
    @delete="emitDelete"
  />
</template>
<style scoped></style>
