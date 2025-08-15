<script setup lang="ts">
const props = defineProps<{ definition: PxComponentDefinition }>()

const emit = defineEmits<{
  (e: 'edit', updatedDefinition: PxComponentDefinition): void
  (e: 'delete', id: string): void
}>()

const isBeingEdited = ref(false)

const editForm = ref({
  name: props.definition.name,
})

function startEdit() {
  isBeingEdited.value = true
}

function confirmEdit() {
  isBeingEdited.value = false
  emit('edit', { ...props.definition, ...editForm.value })
}

function cancelEdit() {
  isBeingEdited.value = !isBeingEdited.value
  editForm.value.name = props.definition.name
}

function emitDelete() {
  emit('delete', props.definition.id)
}
</script>
<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
        <NuxtLink :to="{ name: 'pxcomponentdefinitions-id', params: { id: props.definition.id } }">
          {{ props.definition.name }}
        </NuxtLink>
      </h2>
      <UTextarea v-else v-model="editForm.name" />
    </template>
    Type: {{ definition.type }}
    <template #footer>
      <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
        <UButton color="secondary" variant="soft" @click="startEdit">Rename</UButton>
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
