<script setup lang="ts">
const props = defineProps<{
  definition: PxLockDefinition
  visualizationStyle: 'preview' | 'detailed'
}>()
</script>

<template>
  <PxLockDefinitionCardPreview
    v-if="visualizationStyle === 'preview'"
    :definition="props.definition"
  />

  <PxLockDefinitionCardDetailed v-else :definition="props.definition" />
</template>
<style scoped></style>
