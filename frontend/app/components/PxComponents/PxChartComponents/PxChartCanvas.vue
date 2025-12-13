<script setup lang="ts">
import {
  type NodeDragEvent,
  VueFlow,
  useVueFlow,
  Panel,
  type Connection,
  type EdgeChange,
  type NodeChange,
  type Node,
  type NodeSelectionChange,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { PxChartEdge } from '#components'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { screenToFlowCoordinate } = useVueFlow()

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

const { path, calculatePathFromSelection, resetPathValue, updatePathHighlight } =
  usePxChartPathCalculation(nodes, edges)

const edgeTypes = {
  pxGraph: markRaw(PxChartEdge),
}

// Selected node for context strategy panel
const selectedNodeForAnalysis = ref<{
  nodeId: string
  containerId: string
  nodeName: string
} | null>(null)
const showStrategyPanel = ref(false)

function handleNodeClick(event: { node: Node }) {
  const container = event.node.data as PxChartContainer
  if (container?.content) {
    selectedNodeForAnalysis.value = {
      nodeId: container.content,
      containerId: container.id,
      nodeName: container.name || 'Unknown',
    }
  }
}

function openStrategyPanel() {
  if (selectedNodeForAnalysis.value) {
    showStrategyPanel.value = true
  }
}

function closeStrategyPanel() {
  showStrategyPanel.value = false
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
  updatePath()
}

async function handleDeletePxGraphContainer(containerId: string) {
  await deleteContainer(containerId, true)
  fetchPxChartContainers()
  removeFromSelected(containerId)
}

async function handleUpdatePxGraphContainer(updatedPxChartContainer: Partial<PxChartContainer>) {
  await updateContainer(updatedPxChartContainer)
  fetchPxChartContainers()
}

async function handleAddPxNode(pxGraphContainerId: string, pxNodeId: string) {
  await addNodeToContainer(pxGraphContainerId, pxNodeId)
  fetchPxNodes()
  fetchPxChartContainers()
}

async function handleDeletePxNode(pxGraphContainerId: string) {
  await removeNodeFromContainer(pxGraphContainerId)
  fetchPxNodes()
  fetchPxChartContainers()
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
  fetchPxChartContainers()
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

async function updatePath() {
  if (selectedNodesInOrder.value.length >= 2) {
    await calculatePathFromSelection(selectedNodesInOrder.value)
    await updatePathHighlight()
  }
}

const selectedNodesInOrder: Ref<string[]> = ref([])

async function removeFromSelected(idToRemove: string) {
  selectedNodesInOrder.value = selectedNodesInOrder.value.filter((id) => id != idToRemove)
}

async function onSelectionChange(change: NodeSelectionChange) {
  // update record of selected nodes
  if (change.selected) {
    selectedNodesInOrder.value.push(change.id)
  } else {
    removeFromSelected(change.id)
  }

  // update path based on current selection
  if (selectedNodesInOrder.value.length >= 2) {
    await calculatePathFromSelection(selectedNodesInOrder.value)
  } else {
    await resetPathValue()
  }
  await updatePathHighlight()
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
    @node-click="handleNodeClick"
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

    <!-- Context Strategy Analysis Button -->
    <Panel :position="'top-right'">
      <UTooltip
        :text="selectedNodeForAnalysis ? 'Analyze Node Context' : 'Select a node first'"
        :content="{ align: 'center', side: 'left' }"
      >
        <UButton
          size="lg"
          icon="i-heroicons-cpu-chip"
          color="warning"
          :disabled="!selectedNodeForAnalysis"
          @click="openStrategyPanel"
        >
          Context Analysis
        </UButton>
      </UTooltip>
      <div v-if="selectedNodeForAnalysis" class="mt-2 text-xs text-gray-600 dark:text-gray-400">
        Selected: {{ selectedNodeForAnalysis.nodeName }}
      </div>
    </Panel>
  </VueFlow>

  <!-- Context Strategy Slideover -->
  <USlideover v-model:open="showStrategyPanel" :ui="{ width: 'max-w-lg' }">
    <template #title>
      <div class="flex items-center gap-2">
        <UIcon name="i-heroicons-cpu-chip" />
        Context Strategy Analysis
      </div>
    </template>

    <template #body>
      <ContextStrategyPanel
        v-if="selectedNodeForAnalysis"
        :chart-id="chartId"
        :node-id="selectedNodeForAnalysis.nodeId"
        :node-name="selectedNodeForAnalysis.nodeName"
      />
    </template>

    <template #footer>
      <UButton color="neutral" variant="outline" @click="closeStrategyPanel"> Close </UButton>
    </template>
  </USlideover>

  <div v-if="error" style="color: red; margin-top: 1rem">
    {{ error }}
  </div>
</template>

<style scoped></style>
