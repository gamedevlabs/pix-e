<script setup lang="ts">
const props = defineProps<{ definition: PxKeyDefinition }>()
</script>
<template>
  <UButton :to="{ name: 'pxkeydefinitions-id', params: { id: props.definition.id } }">
    {{ props.definition.name }}</UButton
  >
</template>
<style scoped></style>
