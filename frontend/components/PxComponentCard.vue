<script setup lang="ts">
import PxComponentCardPreview from '~/components/PxComponentCardPreview.vue'
import PxComponentCardDetailed from '~/components/PxComponentCardDetailed.vue'

const props = defineProps<{
  component: PxComponent
  visualizationStyle: 'preview' | 'detailed'
}>()

const emit = defineEmits<{
  (e: 'edit', updatedComponent: PxComponent): void
  (e: 'delete', id: number): void
}>()

function emitDelete() {
  emit('delete', props.component.id)
}
</script>

<template>
  <PxComponentCardPreview v-if="visualizationStyle === 'preview'" :component="component" />

  <PxComponentCardDetailed v-else :component="component">
    <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
  </PxComponentCardDetailed>
</template>
<style scoped></style>
