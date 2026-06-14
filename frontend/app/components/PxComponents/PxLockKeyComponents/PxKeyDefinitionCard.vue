<script setup lang="ts">
const props = defineProps<{
  definition: PxKeyDefinition
  visualizationStyle: 'preview' | 'detailed'
}>()
</script>

<template>
  <PxKeyDefinitionCardPreview
    v-if="visualizationStyle === 'preview'"
    :definition="props.definition"
  />

  <PxKeyDefinitionCardDetailed v-else :definition="props.definition" />
</template>
<style scoped></style>
