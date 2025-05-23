<script setup lang="ts">
const props = defineProps<{
  component: PxComponent
}>()

const emit = defineEmits<{
  (e: 'delete', id: number): void
}>()

function emitDelete() {
  emit('delete', props.component.id)
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 class="font-semibold text-lg">
        <NuxtLink :to="{ name: 'pxcomponents-id', params: { id: props.component.id } }">
          Definition: {{ props.component.definition }}
        </NuxtLink>
      </h2>
    </template>

    <p>Value {{ props.component.value }}</p>
    <p>Node {{ props.component.node }}</p>
    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
      </div>
    </template>
  </UCard>
</template>

<style scoped></style>
