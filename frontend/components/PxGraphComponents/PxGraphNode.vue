<script setup lang="ts">
import { Handle, type NodeProps, Position } from '@vue-flow/core'
import { NodeResizer, type ResizeDragEvent, type ResizeParams } from '@vue-flow/node-resizer'
import '@vue-flow/node-resizer/dist/style.css'

const props = defineProps<NodeProps<PxChartNode>>()
const emit = defineEmits<{
  (e: 'edit', updatedNode: Partial<PxChartNode>): void
  (e: 'delete', id: string): void
}>()

const { updateItem: updatePxChartNode } = usePxChartNodes(props.data.px_chart)

const minWidth = 250
const minHeight = 200

const isBeingEdited = ref(false)
const editForm = ref({
  name: props.data.name,
})

const containsPxNodeData = computed(() => {
  return props.data.content
})

async function handleResizeEnd(eventParams: { event: ResizeDragEvent; params: ResizeParams }) {
  await updatePxChartNode(props.id, {
    layout: {
      position_x: eventParams.params.x,
      position_y: eventParams.params.y,
      width: eventParams.params.width,
      height: eventParams.params.height,
    },
  })
}

function startEdit() {
  isBeingEdited.value = true
}

async function confirmEdit() {
  isBeingEdited.value = false
  emit('edit', { id: props.id as unknown as number, name: editForm.value.name })
}

function cancelEdit() {
  isBeingEdited.value = false
  editForm.value.name = props.data.name
}

async function emitDelete() {
  emit('delete', props.id)
}
</script>

<template>
  <div>
    <UCard class="hover:shadow-lg transition">
      <template #header>
        <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
          {{ props.data.name }}
        </h2>
        <UTextarea v-else v-model="editForm.name" />
      </template>

      <template #footer>
        <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
          <UButton color="secondary" variant="soft" @click="startEdit">Edit</UButton>
          <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
        </div>
        <div v-else class="flex gap-2">
          <UButton color="error" variant="soft" @click="cancelEdit">Cancel</UButton>
          <UButton color="secondary" variant="soft" @click="confirmEdit">Confirm</UButton>
        </div>
      </template>
    </UCard>
    <NodeResizer
      :is-visible="props.selected"
      :min-width="minWidth"
      :min-height="minHeight"
      @resize-end="handleResizeEnd"
    />

    <PxNodeCard v-if="containsPxNodeData" :node="props.data.content!" />

    <Handle id="target-a" type="target" :position="Position.Top" />
    <Handle id="source-b" type="source" :position="Position.Bottom" />
  </div>
</template>

<style scoped></style>
