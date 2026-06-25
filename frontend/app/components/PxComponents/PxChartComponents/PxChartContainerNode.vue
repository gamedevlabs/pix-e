<script setup lang="ts">
import { Handle, type NodeProps, Position } from '@vue-flow/core'
import { NodeResizer, type ResizeDragEvent, type ResizeParams } from '@vue-flow/node-resizer'
import '@vue-flow/node-resizer/dist/style.css'

const props = defineProps<NodeProps<PxChartContainer>>()
const emit = defineEmits<{
  (e: 'delete' | 'switchPxNode', id: string): void
  (e: 'updatePxNode', containerId: string, pxNodeId: string): void
  (e: 'componentsUpdated'): void
}>()

const { updateItem: updatePxChartContainer } = usePxChartContainers(props.data.px_chart)
const { fetchById: getPxNode } = usePxNodes()

const pxNode = ref<PxNode | null>(null)

const cardRef = useTemplateRef('cardRef')
let observer: ResizeObserver

const minWidth = 400
const minHeightGivenContent = computed(() => {
  return cardHeight
})
const cardWidth = ref(0)
const cardHeight = ref(0)

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

async function handleDelete() {
  emit('delete', props.id)
}

async function handleSwitchPxNode() {
  emit('switchPxNode', props.id)
}

async function handleUpdatePxNode() {
  emit('updatePxNode', props.id, pxNode.value?.id)
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

defineShortcuts({
  Delete: () => {
    if (props.selected) {
      handleDelete()
    }
  },
})
</script>

<template>
  <div ref="cardRef">
    <div v-if="pxNode">
      <PxNodeCard
        :node-id="pxNode.id"
        :visualization-style="'detailed'"
        :is-collapsible="true"
        @delete="handleDelete()"
        @switch-node="handleSwitchPxNode()"
        @add-key="handleUpdatePxNode()"
        @delete-key="handleUpdatePxNode()"
        @components-updated="$emit('componentsUpdated')"
      />
    </div>

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
