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
  type Connection,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import PxGraphNode from '~/components/PxGraphComponents/PxGraphNode.vue'
import PxGraphEdge from '~/components/PxGraphComponents/PxGraphEdge.vue'
import { v4 } from 'uuid'
import merge from 'lodash.merge'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { project } = useVueFlow()

// const { layout } = usePxGraphLayout()

const chartId = props.chartId

const { error: pxChartError, fetchById: fetchPxChart } = usePxCharts()
const {
  updateItem: updatePxChartNode,
  createItem: createPxChartNode,
  deleteItem: deletePxChartNode,
} = usePxChartNodes(chartId)
const { createItem: createPxEdge, deleteItem: deletePxEdge } = usePxChartEdges(chartId)

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
        position: { x: n.layout.position_x ?? 100, y: n.layout.position_y ?? 100 },
        height: n.layout.height,
        width: n.layout.width,
        data: { name: n.name, content: n.content, px_chart: n.px_chart },
      }))

      console.log(nodes.value[0])

      edges.value = data.edges.map((e: PxChartEdge) => ({
        id: e.id,
        source: e.source,
        sourceHandle: e.sourceHandle,
        target: e.target,
        targetHandle: e.targetHandle,
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

    // The node movement position update is handled by Vue Flow, and since we double bind
    // the nodes, the changes are also forwarded to our single-source-of truth!
  } catch {
    error.value = 'Failed to update node position'
  }
}

async function addNode(position_x = 0, position_y = 0) {
  const newId = v4()
  const newNodePayload = {
    id: newId,
    name: 'New node',
    content: null,
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
      position: {
        x: newNodePayload.layout.position_x ?? 100,
        y: newNodePayload.layout.position_y ?? 100,
      },
      height: newNodePayload.layout.height,
      width: newNodePayload.layout.width,
      data: { name: newNodePayload.name, content: newNodePayload.content, px_chart: props.chartId },
    })
  } catch {
    alert('Failed to add node: ' + error.value)
  }
}

function onConnect(connection: Connection) {
  const newUuid = v4()
  createPxEdge({
    id: newUuid,
    source: connection.source,
    sourceHandle: connection.sourceHandle,
    target: connection.target,
    targetHandle: connection.targetHandle,
    px_chart: chartId,
  })
    .catch(() => (error.value = 'Failed to create edge'))
    .finally(() => {
      edges.value.push({
        id: newUuid,
        source: connection.source,
        sourceHandle: connection.sourceHandle,
        target: connection.target,
        targetHandle: connection.targetHandle,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
        type: 'pxGraph',
      })
    })
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

  // Remove all edges connected to removed node from local model
  edges.value = edges.value.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
}

async function handleUpdatePxGraphNode(updatedPxChartNode: Partial<PxChartNode>) {
  if (!updatedPxChartNode.id) {
    alert('An update was issued to a node, however, no ID was provided. Aborting.')
    return
  }

  // Here, we have to make sure that properties like name, content, or pxgraph are handled correctly
  // This means, that for the backend, the updatedPxChartNode can just be used, however, for
  // frontend array, these attributes need to be put into data.
  let data = null
  if (updatedPxChartNode.content !== undefined) {
    data = merge(data, { data: { content: updatedPxChartNode.content } })
  }
  if (updatedPxChartNode.name) {
    data = merge(data, { data: { name: updatedPxChartNode.name } })
  }
  if (updatedPxChartNode.px_chart) {
    data = merge(data, { data: { px_chart: updatedPxChartNode.px_chart } })
  }

  // Update node in backend
  await updatePxChartNode(updatedPxChartNode.id!, updatedPxChartNode)

  nodes.value.splice(
    nodes.value.findIndex((node) => node.id === updatedPxChartNode.id),
    1,
    merge(
      nodes.value[nodes.value.findIndex((node) => node.id === updatedPxChartNode.id)],
      updatedPxChartNode,
      data,
    ),
  )
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
