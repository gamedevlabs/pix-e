<script setup lang="ts">
const props = defineProps<{ node: PxNode }>()

function startEdit() {
  console.log('Edit node')
}

function deletePxNode() {
  console.log('Delete node')
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 class="font-semibold text-lg">{{ props.node.name }}</h2>
    </template>
    <p>{{ props.node.description }}</p>
    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton color="secondary" variant="soft" @click="startEdit">Edit</UButton>
        <UButton color="error" variant="soft" @click="deletePxNode()">Delete</UButton>
      </div>
    </template>
  </UCard>
</template>

<style scoped></style>
