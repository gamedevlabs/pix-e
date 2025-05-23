<script setup lang="ts">
const props = defineProps<{
  node: PxNode
  components: Array<PxComponent>
}>()

const emit = defineEmits<{
  (e: 'edit', updatedNode: PxNode): void
  (e: 'delete' | 'addComponent', id: number): void
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
/*
function emitAddComponent() {
  emit('addComponent', props.node.id)
}
*/
function emitDelete() {
  emit('delete', props.node.id)
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
        <NuxtLink :to="{ name: 'pxnodes-id', params: { id: props.node.id } }">
          {{ props.node.name }}
        </NuxtLink>
      </h2>
      <UTextarea v-else v-model="editForm.name" />
    </template>

    <div v-if="!isBeingEdited">
      <p>{{ props.node.description }}</p>
      <br />
      <section class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div v-for="component in props.components" :key="component.id" class="">
          <PxComponentCard visualization-style="preview" :component="component" />
        </div>
      </section>
    </div>
    <UTextarea v-else v-model="editForm.description" />

    <template #footer>
      <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
        <!-- <UButton color="primary" variant="soft" @click="emitAddComponent">Add Component</UButton> -->
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
