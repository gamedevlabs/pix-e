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

const props = defineProps({ chartId: { type: String, default: -1 } })

const { fitView, project } = useVueFlow()

// const { layout } = usePxGraphLayout()

const chartId = props.chartId

const { fetchById: fetchPxChart } = usePxCharts()
const {
  updateItem: updatePxChartNode,
  createItem: createPxNode,
  deleteItem: deletePxNode,
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
      console.log(data.nodes[0])
      nodes.value = data.nodes.map((n: PxChartNode) => ({
        id: String(n.id),
        type: 'pxGraph',
        position: { x: n.layout.position_x, y: n.layout.position_y },
        height: n.layout.height,
        width: n.layout.width,
        data: { name: n.name, content: n.content, px_chart: n.px_chart },
      }))

      edges.value = data.edges.map((e: PxChartEdge) => ({
        id: String(e.id),
        source: String(e.source),
        target: String(e.target),
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
  } catch {
    error.value = 'Failed to update node position'
  }
}

async function addNode(position_x = 0, position_y = 0) {
  const newNodePayload = {
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
    await createPxNode(newNodePayload)
    await loadGraph()
  } catch {
    error.value = 'Failed to add node'
  }
}

function onConnect(params: { source: string; target: string }) {
  createPxEdge({
    source: Number(params.source),
    target: Number(params.target),
    px_chart: Number(chartId),
  })
    .then(loadGraph)
    .catch(() => (error.value = 'Failed to create edge'))
}

/*
async function layoutGraph(direction: string) {
  console.log(direction)
  nodes.value = layout(nodes.value, edges.value, direction)

  await nextTick(() => {
    fitView()
  })
}
*/

async function onNodesChange(changes) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxNode(change.id)
      console.log('node deleted')
    } else if (change.type === 'resize') {
      console.log('node resized')
    }
  }
}

async function handleDeletePxGraphNode(nodeId: string) {
  await deletePxNode(nodeId)

  nodes.value.splice(
    nodes.value.findIndex((node) => node.id === nodeId),
    1,
  )
}

async function handleUpdatePxGraphNode(updatedPxChartNode: Partial<PxChartNode>) {
  console.log(updatedPxChartNode.id)
  await updatePxChartNode(updatedPxChartNode.id!, updatedPxChartNode)

  const updatedNodeIdString = updatedPxChartNode.id as unknown as string

  nodes.value[nodes.value.findIndex((node) => node.id === updatedNodeIdString)] = {
    ...nodes.value[nodes.value.findIndex((node) => node.id === updatedNodeIdString)],
    ...updatedPxChartNode,
  }
}

async function onEdgesChange(changes) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxEdge(change.id)
      console.log('edge deleted')
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
</script>

<template>
  <VueFlow
    :nodes="nodes"
    :edges="edges"
    :edge-types="edgeTypes"
    @node-drag-stop="onNodeDragStop"
    @connect="onConnect"
    @nodes-initialized="fitView()"
    @nodes-change="onNodesChange"
    @edges-change="onEdgesChange"
    @pane-context-menu="onContextMenu($event)"
  >
    <Background />

    <template #node-pxGraph="customNodeProps">
      <PxGraphNode
        v-bind="customNodeProps"
        @delete="handleDeletePxGraphNode"
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
