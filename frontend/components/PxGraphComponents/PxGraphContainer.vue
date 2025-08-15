<script setup lang="ts">
import { Handle, type NodeProps, Position } from '@vue-flow/core'
import { NodeResizer, type ResizeDragEvent, type ResizeParams } from '@vue-flow/node-resizer'
import '@vue-flow/node-resizer/dist/style.css'
import { LazyPxGraphComponentsPxGraphContainerAddPxNodeForm } from '#components'

const props = defineProps<NodeProps<PxChartContainer>>()
const emit = defineEmits<{
  (e: 'edit', updatedNode: Partial<PxChartContainer>): void
  (e: 'delete' | 'deletePxNode', id: string): void
  (e: 'addPxNode', pxGraphContainerId: string, pxNodeId: string): void
}>()

const { updateItem: updatePxChartContainer } = usePxChartContainers(props.data.px_chart)
const { fetchById: getPxNode } = usePxNodes()

const overlay = useOverlay()
const modal = overlay.create(LazyPxGraphComponentsPxGraphContainerAddPxNodeForm)

const isBeingEdited = ref(false)
const editForm = ref({
  name: props.data.name,
})

const pxNode = ref<PxNode | null>(null)

const cardRef = useTemplateRef('cardRef')
let observer: ResizeObserver

const minWidth = 400
const minHeightGivenContent = computed(() => {
  return cardHeight
})
const cardWidth = ref(0)
const cardHeight = ref(0)

const containsPxNodeData = computed(() => {
  return props.data.content
})

watch(containsPxNodeData, () => {
  loadContent()
})

onMounted(() => {
  loadContent()
  listenToResizing()
})

onBeforeUnmount(() => {
  if (observer && cardRef.value) {
    observer.unobserve(cardRef.value)
  }
})

async function loadContent() {
  if (!containsPxNodeData.value) {
    pxNode.value = null
    return
  }

  if (!props.data || !props.data.content) {
    return
  }

  pxNode.value = await getPxNode(props.data.content!)
}

async function handleResizeEnd(eventParams: { event: ResizeDragEvent; params: ResizeParams }) {
  await updatePxChartContainer(props.id, {
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

async function handleAddPxNode() {
  const nodeId = await modal.open().result

  if (!nodeId) return

  emit('addPxNode', props.id, nodeId)
}

async function removePxNode() {
  emit('deletePxNode', props.id)
}

function listenToResizing() {
  if (cardRef.value) {
    observer = new ResizeObserver((entries) => {
      for (let i = 0; i < entries.length; i++) {
        const { width, height } = entries[i].contentRect
        cardWidth.value = width
        cardHeight.value = height
      }
    })
    observer.observe(cardRef.value)
  }
}
</script>

<template>
  <div ref="cardRef">
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
        <div v-else class="flex justify-end gap-2">
          <UButton color="secondary" variant="soft" @click="confirmEdit">Confirm</UButton>
          <UButton color="error" variant="soft" @click="cancelEdit">Cancel</UButton>
        </div>
      </template>
    </UCard>

    <NodeResizer
      :is-visible="props.selected"
      :min-width="minWidth"
      :min-height="minHeightGivenContent.value"
      @resize-end="handleResizeEnd"
    />

    <Handle id="target-a" type="target" :position="Position.Top" />
    <Handle id="target-b" type="target" :position="Position.Right" />
    <Handle id="target-c" type="target" :position="Position.Bottom" />
    <Handle id="target-d" type="target" :position="Position.Left" />
    <Handle id="source-a" type="source" :position="Position.Top" />
    <Handle id="source-b" type="source" :position="Position.Right" />
    <Handle id="source-c" type="source" :position="Position.Bottom" />
    <Handle id="source-d" type="source" :position="Position.Left" />
  </div>
</template>

<style scoped></style>
