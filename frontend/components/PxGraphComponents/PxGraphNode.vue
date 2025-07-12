<script setup lang="ts">
import { Handle, type NodeProps, Position } from '@vue-flow/core'
import { NodeResizer, type ResizeDragEvent, type ResizeParams } from '@vue-flow/node-resizer'
import '@vue-flow/node-resizer/dist/style.css'
import { LazyPxGraphComponentsPxGraphNodeAddPxNodeForm } from '#components'

const props = defineProps<NodeProps<PxChartNode>>()
const emit = defineEmits<{
  (e: 'edit', updatedNode: Partial<PxChartNode>): void
  (e: 'delete' | 'deletePxNode', id: string): void
  (e: 'addPxNode', pxGraphNodeId: string, pxNodeId: string): void
}>()

const { updateItem: updatePxChartNode } = usePxChartNodes(props.data.px_chart)
const { fetchById: getPxNode } = usePxNodes()

const overlay = useOverlay()
const modal = overlay.create(LazyPxGraphComponentsPxGraphNodeAddPxNodeForm)

const minWidth = 250
const minHeight = 100

const isBeingEdited = ref(false)
const editForm = ref({
  name: props.data.name,
})

const pxNode = ref<PxNode | null>(null)

const containsPxNodeData = computed(() => {
  return props.data.content
})

watch(containsPxNodeData, () => {
  loadContent()
})

onMounted(() => {
  loadContent()
})

async function loadContent() {
  if (!containsPxNodeData.value) {
    pxNode.value = null
    return
  }

  if(!props.data || !props.data.content) {
    return
  }

  pxNode.value = await getPxNode(props.data.content!)
}

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
  emit('edit', { id: props.id, name: editForm.value.name })
}

function cancelEdit() {
  isBeingEdited.value = false
  editForm.value.name = props.data.name
}

async function emitDelete() {
  emit('delete', props.id)
}

async function removePxNode() {
  emit('deletePxNode', props.id)
}

async function handleAddPxNode() {
  const nodeId = await modal.open().result

  if (!nodeId) return

  emit('addPxNode', props.id, nodeId)
}
</script>

<template>
  <div>
    <UCard class="hover:shadow-lg transition">
      <template #header>
        <h2 v-if="!isBeingEdited" class="font-semibold text-lg">{{ props.data.name }}</h2>
        <UTextarea v-else v-model="editForm.name" :rows="1" />
      </template>

      <template #default>
        <div v-if="pxNode">
          <PxNodeCard :node="pxNode" :visualization-style="'preview'" />
        </div>
        <div class="flex flex-wrap justify-end gap-2">
          <UButton
            v-if="!containsPxNodeData"
            color="primary"
            variant="soft"
            @click="handleAddPxNode"
            >Add Px Node</UButton
          >
        </div>
      </template>

      <template #footer>
        <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
          <UButton v-if="containsPxNodeData" color="primary" variant="soft" @click="removePxNode()"
            >Remove Px Node</UButton
          >
          <UButton color="secondary" variant="soft" @click="startEdit">Edit Name</UButton>
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

    <Handle id="target-a" type="target" :position="Position.Left" />
    <Handle id="source-b" type="source" :position="Position.Right" />
  </div>
</template>

<style scoped></style>
