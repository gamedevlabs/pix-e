<script setup lang="ts">
const props = defineProps<{ definition: PxLockDefinition }>()
</script>
<template>
  <UButton :to="{ name: 'pxlockdefinitions-id', params: { id: props.definition.id } }">
    {{ props.definition.name }}</UButton
  >
</template>
<style scoped></style>
