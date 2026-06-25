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
  <div ref="cardRef" class="px-node group">
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

    <Handle id="target-a" class="px-node-handle" type="target" :position="Position.Top" />
    <Handle id="target-b" class="px-node-handle" type="target" :position="Position.Right" />
    <Handle id="target-c" class="px-node-handle" type="target" :position="Position.Bottom" />
    <Handle id="target-d" class="px-node-handle" type="target" :position="Position.Left" />
    <Handle id="source-a" class="px-node-handle" type="source" :position="Position.Top" />
    <Handle id="source-b" class="px-node-handle" type="source" :position="Position.Right" />
    <Handle id="source-c" class="px-node-handle" type="source" :position="Position.Bottom" />
    <Handle id="source-d" class="px-node-handle" type="source" :position="Position.Left" />
  </div>
</template>

<style scoped>
.px-node {
  position: relative;
  padding: 12px;
  margin: -12px;
}

.px-node::before {
  content: "";
  position: absolute;
  inset: -16px; /* expand hover area by 16px on all sides */
  z-index: -1
}

.px-node-handle {
  width: 16px;
  height: 16px;

  background: color-mix(in srgb, var(--ui-primary) 25%, transparent);
  border: 2px solid var(--ui-primary);

  opacity: 0;
  pointer-events: none;

  transition: all .15s ease;
}

.px-node-handle::after {
  content: "";
  position: absolute;
  inset: -16px;
}

.px-node:hover .px-node-handle,
.px-node:focus-within .px-node-handle {
  opacity: 1;
  pointer-events: auto;
}

.px-node-handle:hover {
  background: var(--ui-primary);
}

</style>
