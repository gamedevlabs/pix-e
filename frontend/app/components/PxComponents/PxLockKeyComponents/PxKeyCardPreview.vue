<script setup lang="ts">
const props = defineProps<{ pxkey: PxKey; definition: PxKeyDefinition; readonly: boolean }>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

function emitDelete() {
  emit('delete', props.pxkey.id)
}
</script>
<template>
  <UFieldGroup>
    <UButton :to="{ name: 'pxkeys-id', params: { id: props.pxkey.id } }" variant="outline">
      <p>{{ props.pxkey.count }}x</p>
      <p class="font-semibold">{{ props.definition.name }}</p></UButton
    >
    <UButton
      v-if="!readonly"
      color="error"
      icon="i-lucide-trash-2"
      :on-click="emitDelete"
      variant="subtle"
    />
  </UFieldGroup>
</template>
<style scoped></style>
