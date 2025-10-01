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
import PxChartContainer from '~/components/PxChartComponents/PxChartContainer.vue'
import PxChartEdge from '~/components/PxChartComponents/PxChartEdge.vue'
import PxChartContainerNode from '~/components/PxChartComponents/PxChartContainerNode.vue'

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
  applyDefaultNodeChanges,
  addNodeToContainer,
  removeNodeFromContainer,
  deleteContainer,
  addEdge,
  applyDefaultEdgeChanges,
  deleteEdge,
} = usePxChartsCanvasApi(chartId)

const edgeTypes = {
  pxGraph: markRaw(PxChartEdge),
}

onMounted(() => {
  loadGraph()
})

async function onNodeDragStop(event: NodeDragEvent) {
  for (const node of event.nodes) {
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
}

async function onConnect(connection: Connection) {
  await addEdge(connection)
}

async function handleDeletePxGraphContainer(containerId: string) {
  await deleteContainer(containerId, true)
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

// We disabled the automatic behavior of Vue Flow, therefore, we need to handle all
// changes either ourselves, or let Vue Flow handle them explicitly
async function onNodesChange(changes: NodeChange[]) {
  const defaultChanges: NodeChange[] = []
  for (const change of changes) {
    switch (change.type) {
      // Adding nodes is already handled in addNode
      case 'add':
        break
      case 'remove':
        await deleteContainer(change.id)
        break
      case 'position':
        if (change.dragging) {
          defaultChanges.push(change)
        }
        break
      case 'dimensions':
        defaultChanges.push(change)
        break
      case 'select':
        defaultChanges.push(change)
        break
    }
  }

  applyDefaultNodeChanges(defaultChanges)
}

async function onEdgesChange(changes: EdgeChange[]) {
  const defaultChanges: EdgeChange[] = []
  for (const change of changes) {
    switch (change.type) {
      // Handled in onConnect
      case 'add':
        break
      case 'select':
        defaultChanges.push(change)
        break
      case 'remove':
        await deleteEdge(change.id)
        break
    }
  }

  applyDefaultEdgeChanges(defaultChanges)
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
    :apply-default="false"
    @node-drag-stop="onNodeDragStop"
    @connect="onConnect"
    @nodes-change="onNodesChange"
    @edges-change="onEdgesChange"
    @pane-context-menu="onContextMenu($event)"
  >
    <!--@nodes-initialized="fitView()"-->

    <Background />

    <template #node-pxEmpty="customNodeProps">
      <PxChartContainer
        v-bind="customNodeProps"
        @delete="handleDeletePxGraphContainer"
        @add-px-node="handleAddPxNode"
        @edit="handleUpdatePxGraphContainer"
      />
    </template>

    <template #node-pxNode="customNodeProps">
      <PxChartContainerNode
        v-bind="customNodeProps"
        @remove-px-node="handleDeletePxNode"
        @delete="handleDeletePxGraphContainer"
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
