<script setup lang="ts">
import { LazyPxComponentCreationForm } from '#components'

const props = defineProps<{
  node: PxNode
}>()

const emit = defineEmits<{
  (e: 'update', updatedNode: PxNode): void
  (e: 'delete', nodeId: string): void
  (e: 'deleteComponent' | 'addComponent', nodeId: string, componentId: string): void
}>()

const isBeingEdited = ref(false)

const overlay = useOverlay()
const modal = overlay.create(LazyPxComponentCreationForm)

const editForm = ref({
  name: props.node.name,
  description: props.node.description,
})

function startEdit() {
  editForm.value = { ...props.node }
  isBeingEdited.value = true
}

function confirmEdit() {
  isBeingEdited.value = false
  emit('update', { ...props.node, ...editForm.value })
}

function cancelEdit() {
  isBeingEdited.value = !isBeingEdited.value
  editForm.value.name = props.node.name
  editForm.value.description = props.node.description
}

function emitDelete() {
  emit('delete', props.node.id)
}

function handleDeleteComponent(componentId: string) {
  emit('deleteComponent', props.node.id, componentId)
}

async function handleAddComponent() {
  const { nodeId, componentId } = await modal.open({ selectedNodeId: props.node.id }).result

  emit('addComponent', nodeId, componentId)
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

    <template #default>
      <div v-if="!isBeingEdited">
        <h2 class="font-semibold text-lg mb-2">Description</h2>
        <p>{{ props.node.description }}</p>
        <br />
        <h2 v-if="node.components.length === 0" class="italic">This node has no components.</h2>
        <h2 v-else class="font-semibold text-lg mb-2">Components</h2>
        <section class="grid grid-cols-1 gap-6">
          <div v-for="component in node.components" :key="component.id">
            <PxComponentCard
              visualization-style="preview"
              :component="component"
              @delete="handleDeleteComponent"
            />
          </div>
        </section>
        <br />
        <h2 v-if="node.charts.length === 0" class="italic">
          This node is not associated to any charts.
        </h2>
        <div v-else>
          <h2 class="font-semibold text-lg mb-2">Associated Charts</h2>
          <section class="grid grid-cols-1 gap-6">
            <div v-for="chart in node.charts" :key="chart.id">
              <PxChartCard :px-chart="chart" :visualization-style="'preview'" />
            </div>
          </section>
        </div>
      </div>
      <UTextarea v-else v-model="editForm.description" />
    </template>

    <template #footer>
      <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
        <UButton color="primary" variant="soft" @click="handleAddComponent">Add Component</UButton>
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
