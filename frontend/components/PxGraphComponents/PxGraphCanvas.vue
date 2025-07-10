<script setup lang="ts">
import {
  type Edge,
  MarkerType,
  type Node,
  type NodeDragEvent,
  VueFlow,
  useVueFlow,
  Panel,
  PanelPosition,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import PxGraphNode from '~/components/PxGraphComponents/PxGraphNode.vue'
import PxGraphEdge from '~/components/PxGraphComponents/PxGraphEdge.vue'
import { v4 } from 'uuid'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { fitView, project, updateNode } = useVueFlow()

// const { layout } = usePxGraphLayout()

const chartId = props.chartId

const { fetchById: fetchPxChart } = usePxCharts()
const {
  items: allPxChartNodes,
  updateItem: updatePxChartNode,
  createItem: createPxChartNode,
  deleteItem: deletePxChartNode,
} = usePxChartNodes(chartId)
const { createItem: createPxEdge, deleteItem: deletePxEdge } = usePxChartEdges(chartId)
const { fetchById: getPxNode } = usePxNodes()

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

/*
const nodeTypes = {
  pxGraph: markRaw(PxGraphNode),
}
*/

const edgeTypes = {
  pxGraph: markRaw(PxGraphEdge),
}

// Load graph with Vue Flow shape
async function loadGraph() {
  loading.value = true
  try {
    const data = await fetchPxChart(chartId)
    if (data) {
      nodes.value = data.nodes.map((n: PxChartNode) => ({
        id: n.id,
        type: 'pxGraph',
        position: { x: n.layout.position_x ?? 100, y: n.layout.position_y ?? 100},
        height: n.layout.height,
        width: n.layout.width,
        data: { name: n.name, content: n.content, px_chart: n.px_chart },
      }))

      edges.value = data.edges.map((e: PxChartEdge) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
        type: 'pxGraph',
      }))
    }
  } catch (e) {
    alert('Problem when getting graph content: ' + e.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadGraph()
})

/*
const oneNodeIsSelected = computed(() => {
  return getSelectedElements.value.length == 1 && isNode(getSelectedElements.value[0])
})

const oneEdgeIsSelected = computed(() => {
  return getSelectedElements.value.length == 1 && isEdge(getSelectedElements.value[0])
})

const multipleElementsSelected = computed(() => {
  return getSelectedElements.value.length > 1
})
*/

async function onNodeDragStop(event: NodeDragEvent) {
  try {
    const node = event.node
    await updatePxChartNode(node.id, {
      layout: {
        position_x: node.position.x,
        position_y: node.position.y,
        width: node.width as number,
        height: node.height as number,
      },
    })

    // Update node in local nodes-array
    // const indexOf = nodes.value.findIndex((node) => node.id === event.node.id)
    // nodes.value.splice(
    //   indexOf,
    //   1, {...nodes.value[indexOf], position: {x: node.position.x, y: node.position.y},}
    // )
  } catch {
    error.value = 'Failed to update node position'
  }
}

async function addNode(position_x = 0, position_y = 0) {
  const newId = v4()
  const newNodePayload = {
    id: newId,
    name: 'New node',
    layout: {
      position_x: position_x,
      position_y: position_y,
      width: 100,
      height: 100,
    },
  }
  try {
    await createPxChartNode(newNodePayload)

    nodes.value.push({
      id: newId,
      type: 'pxGraph',
      position: { x: newNodePayload.layout.position_x ?? 100, y: newNodePayload.layout.position_y ?? 100},
      height: newNodePayload.layout.height,
      width: newNodePayload.layout.width,
      data: { name: newNodePayload.name, content: newNodePayload.content, px_chart: props.chartId },
    })
  } catch {
    alert("Failed to add node: " + error.value)
  }
}

function onConnect(params: { source: string; target: string }) {
  createPxEdge({
    source: params.source,
    target: params.target,
    px_chart: chartId,
  })
    .then(loadGraph)
    .catch(() => (error.value = 'Failed to create edge'))
}

/*
async function layoutGraph(direction: string) {
  nodes.value = layout(nodes.value, edges.value, direction)

  await nextTick(() => {
    fitView()
  })
}
*/

async function onNodesChange(changes) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxChartNode(change.id)
    }
  }
}

async function handleDeletePxGraphNode(nodeId: string) {
  await deletePxChartNode(nodeId)

  nodes.value.splice(
    nodes.value.findIndex((node) => node.id === nodeId),
    1,
  )
}

async function handleUpdatePxGraphNode(updatedPxChartNode: Partial<PxChartNode>) {
  // Update node in backend
  await updatePxChartNode(updatedPxChartNode.id!, updatedPxChartNode)

  // Update node in graph view
  const updatedNodeIdString = updatedPxChartNode.id as unknown as string
  updateNode(updatedNodeIdString, { data: updatedPxChartNode})

  nodes.value[nodes.value.findIndex((node) => node.id === updatedNodeIdString)] = {
    ...nodes.value[nodes.value.findIndex((node) => node.id === updatedNodeIdString)],
    ...updatedPxChartNode,
  }
}

async function onEdgesChange(changes) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxEdge(change.id)
    }
  }
}

function onContextMenu(mouseEvent: MouseEvent) {
  // prevent the browser's default menu
  mouseEvent.preventDefault()
  // for now, just create node
  const pos = project({ x: mouseEvent.x, y: mouseEvent.y })
  addNode(pos.x, pos.y)
}

async function handleAddPxNode(pxGraphNodeId: string, pxNodeId: string) {
  const updatedPxGraphNodeContent = {
    id: pxGraphNodeId,
    content: pxNodeId,
  }

  await handleUpdatePxGraphNode(updatedPxGraphNodeContent)
}

async function handleDeletePxNode(pxGraphNodeId: string) {
  const updatedPxGraphNodeContent = {
    id: pxGraphNodeId,
    content: null,
  }

  await handleUpdatePxGraphNode(updatedPxGraphNodeContent)
}
</script>

<template>
  <VueFlow
    v-model:nodes="nodes"
    :edges="edges"
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
      <PxGraphNode
        v-bind="customNodeProps"
        @delete-px-node="handleDeletePxNode"
        @delete="handleDeletePxGraphNode"
        @add-px-node="handleAddPxNode"
        @edit="handleUpdatePxGraphNode"
      />
    </template>

    <Panel :position="PanelPosition.BottomLeft">
      <UTooltip text="Create Node" :content="{ align: 'center', side: 'right' }">
        <UButton size="xl" icon="i-lucide-plus" color="primary" @click="addNode" />
      </UTooltip>
    </Panel>
  </VueFlow>

  <div v-if="error" style="color: red; margin-top: 1rem">
    {{ error }}
  </div>
</template>

<style scoped></style>
