<script setup lang="ts">
import { useRoute } from 'vue-router'
import { VueFlow, type NodeDragEvent, type Node, type Edge } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import PxGraphNode from '~/components/PxGraphNodes/PxGraphNode.vue'

const route = useRoute()
const chartId = route.params.id as unknown as number

const { fetchById: fetchPxChart } = usePxCharts()
const { updateItem: updatePxNode, createItem: createPxNode } = usePxChartNodes(chartId)
const { createItem: createPxEdge } = usePxChartEdges(chartId)

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const nodeTypes = {
  pxGraph: markRaw(PxGraphNode),
}

// Load graph with Vue Flow shape
async function loadGraph() {
  loading.value = true
  try {
    const data = await fetchPxChart(chartId)
    if (data) {
      // Map backend nodes to Vue Flow nodes
      nodes.value = data.nodes.map((n: PxChartNode) => ({
        id: String(n.id),
        type: 'pxGraph',
        position: { x: n.position_x, y: n.position_y },
        data: { name: n.name, content: n.content },
      }))

      edges.value = data.edges.map((e: PxChartEdge) => ({
        id: String(e.id),
        source: String(e.source),
        target: String(e.target),
        type: 'default',
      }))
    }
  } catch (e) {
    alert(e.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadGraph()
})

async function onNodeDragStop(event: NodeDragEvent) {
  try {
    const node = event.node
    console.log(node)
    await updatePxNode(node.id, {
      position_x: node.position.x,
      position_y: node.position.y,
    })
  } catch {
    error.value = 'Failed to update node position'
  }
}

async function addNode() {
  const newNodePayload = {
    name: 'New node',
    content: JSON.parse('{}'),
    position_x: 200,
    position_y: 200,
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
</script>

<template>
  <div>
    <h2>PxChart {{ chartId }}</h2>

    <div v-for="node in nodes" :key="node.id">
      {{ node }}
    </div>

    <div v-for="edge in edges" :key="edge.id">
      {{ edge }}
    </div>

    <div>
      <u-button @click="addNode">Add Node</u-button>
    </div>

    <div style="height: 600px; border: 2px solid #ccc">
      <VueFlow
        :nodes="nodes"
        :edges="edges"
        :node-types="nodeTypes"
        @node-drag-stop="onNodeDragStop"
        @connect="onConnect"
      >
        <Background />
      </VueFlow>
    </div>

    <div v-if="error" style="color: red; margin-top: 1rem">
      {{ error }}
    </div>
  </div>
</template>

<style scoped>
@import '@vue-flow/core/dist/style.css';

@import '@vue-flow/core/dist/theme-default.css';
</style>
