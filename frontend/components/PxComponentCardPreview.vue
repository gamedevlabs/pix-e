<script setup lang="ts">
const props = defineProps<{ component: PxComponent; definition: PxComponentDefinition }>()
</script>
<template>
  <UButton :to="{ name: 'pxcomponents-id', params: { id: props.component.id } }">
    {{ props.definition.name }} <br />
    {{ props.component.value }}</UButton
  >
</template>
<style scoped></style>
