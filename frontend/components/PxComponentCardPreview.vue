<script setup lang="ts">
const props = defineProps<{ component: PxComponent; definition: PxComponentDefinition }>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

function emitDelete() {
  emit('delete', props.component.id)
}
</script>
<template>
  <div class="flex flex-wrap justify-normal gap-2">
    <UButton :to="{ name: 'pxcomponents-id', params: { id: props.component.id } }">
      {{ props.definition.name }} <br />
      {{ props.component.value }}</UButton
    >
    <UButton color="error" icon="i-lucide-trash-2" :on-click="emitDelete" />
  </div>
</template>
<style scoped></style>
