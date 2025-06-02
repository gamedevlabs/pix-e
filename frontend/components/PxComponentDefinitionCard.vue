<script setup lang="ts">
const props = defineProps<{
  definition: PxComponentDefinition
  visualizationStyle: 'preview' | 'detailed'
}>()
</script>

<template>
  <PxComponentDefinitionCardPreview
    v-if="visualizationStyle === 'preview'"
    :definition="props.definition"
  />

  <PxComponentDefinitionCardDetailed v-else :definition="props.definition" />
</template>
<style scoped></style>
