<script setup lang="ts">
const props = defineProps<{ node: PxNode }>()

const emit = defineEmits<{
  (e: 'edit', updatedNode: PxNode): void
  (e: 'delete', id: number): void
}>()

const isBeingEdited = ref(false)

const editForm = ref({
  name: props.node.name,
  description: props.node.description,
})

function startEdit() {
  isBeingEdited.value = true
}

function confirmEdit() {
  isBeingEdited.value = false
  emit('edit', { ...props.node, ...editForm.value })
}

function cancelEdit() {
  isBeingEdited.value = !isBeingEdited.value
  editForm.value.name = props.node.name
  editForm.value.description = props.node.description
}

function emitDelete() {
  emit('delete', props.node.id)
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 v-if="!isBeingEdited" class="font-semibold text-lg">{{ props.node.name }}</h2>
      <UTextarea v-else v-model="editForm.name" />
    </template>

    <p v-if="!isBeingEdited">{{ props.node.description }}</p>
    <UTextarea v-else v-model="editForm.description" />

    <template #footer>
      <div v-if="!isBeingEdited" class="flex justify-end gap-2">
        <UButton color="secondary" variant="soft" @click="startEdit">Edit</UButton>
        <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
      </div>
      <div v-else class="flex gap-2">
        <UButton color="error" variant="soft" @click="cancelEdit">Cancel</UButton>
        <UButton color="secondary" variant="soft" @click="confirmEdit">Confirm</UButton>
      </div>
    </template>
  </UCard>
</template>

<style scoped></style>
