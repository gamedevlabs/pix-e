<script setup lang="ts">
import {
  type NodeDragEvent,
  VueFlow,
  useVueFlow,
  Panel,
  type Connection,
  type EdgeChange,
  type NodeChange,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import PxGraphContainer from '~/components/PxGraphComponents/PxGraphContainer.vue'
import PxGraphEdge from '~/components/PxGraphComponents/PxGraphEdge.vue'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { screenToFlowCoordinate } = useVueFlow()

const chartId = props.chartId

const {
  nodes,
  edges,
  error,
  pxChartError,
  loadGraph,
  addContainer,
  updateContainer,
  addNodeToContainer,
  removeNodeFromContainer,
  deleteContainer,
  addEdge,
  deleteEdge,
} = usePxChartsCanvasApi(chartId)

const edgeTypes = {
  pxGraph: markRaw(PxGraphEdge),
}

onMounted(() => {
  loadGraph()
})

async function onNodeDragStop(event: NodeDragEvent) {
  const node = event.node
  await updateContainer({
    id: node.id,
    layout: {
      position_x: node.position.x,
      position_y: node.position.y,
      width: node.width as number,
      height: node.height as number,
    },
  })
}

async function onConnect(connection: Connection) {
  await addEdge(connection)
}

async function handleDeletePxGraphContainer(containerId: string) {
  await deleteContainer(containerId)
}

async function handleUpdatePxGraphContainer(updatedPxChartContainer: Partial<PxChartContainer>) {
  await updateContainer(updatedPxChartContainer)
}

async function handleAddPxNode(pxGraphContainerId: string, pxNodeId: string) {
  await addNodeToContainer(pxGraphContainerId, pxNodeId)
}

async function handleDeletePxNode(pxGraphContainerId: string) {
  await removeNodeFromContainer(pxGraphContainerId)
}

async function onNodesChange(changes: NodeChange[]) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deleteContainer(change.id)
    }
  }
}

async function onEdgesChange(changes: EdgeChange[]) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deleteEdge(change.id)
    }
  }
}

async function onContextMenu(mouseEvent: MouseEvent) {
  // prevent the browser's default menu
  mouseEvent.preventDefault()
  // for now, just create a container
  const pos = screenToFlowCoordinate({ x: mouseEvent.x, y: mouseEvent.y })
  await addContainer(pos.x, pos.y)
}
</script>

<template>
  <div v-if="pxChartError">
    <div v-if="pxChartError.response?.status === 403">You do not have access to this graph.</div>
    <div v-if="pxChartError.response?.status === 404">This graph does not exist.</div>
  </div>
  <VueFlow
    v-else
    v-model:nodes="nodes"
    v-model:edges="edges"
    :edge-types="edgeTypes"
    @node-drag-stop="onNodeDragStop"
    @connect="onConnect"
    @nodes-change="onNodesChange"
    @edges-change="onEdgesChange"
    @pane-context-menu="onContextMenu($event)"
  >
    <!--@nodes-initialized="fitView()"-->

    <Background />

    <template #node-pxGraph="customNodeProps">
      <PxGraphContainer
        v-bind="customNodeProps"
        @delete-px-node="handleDeletePxNode"
        @delete="handleDeletePxGraphContainer"
        @add-px-node="handleAddPxNode"
        @edit="handleUpdatePxGraphContainer"
      />
    </template>

    <Panel :position="'bottom-left'">
      <UTooltip text="Create Node" :content="{ align: 'center', side: 'right' }">
        <UButton size="xl" icon="i-lucide-plus" color="primary" @click="addContainer(0, 0)" />
      </UTooltip>
    </Panel>
  </VueFlow>

  <div v-if="error" style="color: red; margin-top: 1rem">
    {{ error }}
  </div>
</template>

<style scoped></style>
