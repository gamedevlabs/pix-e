<script setup lang="ts">
const props = defineProps<{ definition: PxComponentDefinition }>()
</script>
<template>
  <UButton :to="{ name: 'pxcomponentdefinitions-id', params: { id: props.definition.id } }">
    {{ props.definition.name }}</UButton
  >
</template>
<style scoped></style>
