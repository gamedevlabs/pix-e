<script setup lang="ts">
const props = defineProps<{
  pxkey: PxKey
  definition: PxKeyDefinition
  node: PxNode
}>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

function emitDelete() {
  emit('delete', props.pxkey.id)
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 class="font-semibold text-lg">
        <NuxtLink :to="{ name: 'pxkeys-id', params: { id: props.pxkey.id } }">
          Definition: {{ props.definition.name }}
        </NuxtLink>
      </h2>
    </template>

    <template #default>
      <h2 class="font-semibold text-lg mb-2">Count</h2>
      <p>{{ props.pxkey.count }}</p>
      <br />
      <h2 class="font-semibold mb-2">Associated Node</h2>
      <PxNodeCard :node-id="props.node.id" :visualization-style="'preview'" />
    </template>

    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
      </div>
    </template>
  </UCard>
</template>

<style scoped></style>
