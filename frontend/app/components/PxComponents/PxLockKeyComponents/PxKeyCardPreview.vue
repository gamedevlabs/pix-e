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
    <UTooltip :text="props.definition.name">
      <UButton :to="{ name: 'pxkeys-id', params: { id: props.pxkey.id } }" variant="outline" size="lg">
        <p>{{ props.pxkey.count }}x</p>
        <p>{{ props.definition.symbol }}</p></UButton
      >
    </UTooltip>
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
