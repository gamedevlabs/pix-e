<script setup lang="ts">
const props = defineProps<{ component: PxComponent }>()
</script>
<template>
  <ULink to="{ name: 'pxcomponents-id', params: { id: props.component.id } }">
    <UButton> {{ props.component.definition }}</UButton>
  </ULink>
</template>
<style scoped></style>
