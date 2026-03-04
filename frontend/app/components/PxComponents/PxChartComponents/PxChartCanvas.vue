<script setup lang="ts">
import {
  type NodeDragEvent,
  VueFlow,
  useVueFlow,
  Panel,
  type Connection,
  type EdgeChange,
  type NodeChange,
  type NodeSelectionChange,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { PxChartEdge } from '#components'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { screenToFlowCoordinate, getSelectedNodes } = useVueFlow()

const chartId = props.chartId

const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()
const { items: pxComponentDefinitions, fetchAll: fetchPxComponentDefinitions } =
  usePxComponentDefinitions()

const { items: pxChartContainers, fetchAll: fetchPxChartContainers } = usePxChartContainers(
  props.chartId,
)

const {
  nodes,
  edges,
  error,
  path,
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
  calculatePathFromSelection,
  resetPath,
  highlightPath,
} = usePxChartsCanvasApi(chartId)

const edgeTypes = {
  pxGraph: markRaw(PxChartEdge),
}

onMounted(() => {
  loadGraph()
  fetchPxNodes()
  fetchPxComponents()
  fetchPxComponentDefinitions()
  fetchPxChartContainers()
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
  fetchPxChartContainers()
}

async function handleUpdatePxGraphContainer(updatedPxChartContainer: Partial<PxChartContainer>) {
  await updateContainer(updatedPxChartContainer)
  fetchPxChartContainers()
}

async function handleAddPxNode(pxGraphContainerId: string, pxNodeId: string) {
  await addNodeToContainer(pxGraphContainerId, pxNodeId)
  fetchPxNodes()
}

async function handleDeletePxNode(pxGraphContainerId: string) {
  await removeNodeFromContainer(pxGraphContainerId)
  fetchPxNodes()
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
        await onSelectionChange(change)
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

const pxNodeIdsInPath = computed(() => {
  const nodes: Array<string | null> = []
  path.value.forEach((containerId) => {
    const container = pxChartContainers.value.find((container) => container.id === containerId)
    if (container) {
      nodes.push(container.content)
    }
  })

  return nodes
})

const pxNodesInChart = computed(() => {
    const ids = nodes.value.map((vueNode) => vueNode.data.content)
    return pxNodes.value.filter((pxN) => ids.includes(pxN.id))
})

async function onSelectionChange(change: NodeSelectionChange) {
  // do something when selected nodes/edges changed
  const previouslySelectedIds = getSelectedNodes.value.map((gn) => gn.id)
  if (
    previouslySelectedIds.length >= 1 &&
    previouslySelectedIds[0] &&
    previouslySelectedIds[0] != change.id &&
    !previouslySelectedIds.includes(change.id) &&
    change.selected
  ) {
    const ids = [...previouslySelectedIds, change.id]
    await calculatePathFromSelection(ids)
    await highlightPath()
  } else {
    await resetPath()
  }
}
</script>

<template>
  <PxDiagrams 
    :nodes-in-path="pxNodeIdsInPath" 
    :px-nodes="pxNodesInChart"
    :px-components="pxComponents"
    :px-component-definitions="pxComponentDefinitions"
  />
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
