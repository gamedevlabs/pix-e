<script setup lang="ts">
import {
  type Edge,
  MarkerType,
  type Node,
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
import { v4 } from 'uuid'
import merge from 'lodash.merge'

const props = defineProps({ chartId: { type: String, default: -1 } })

const { screenToFlowCoordinate } = useVueFlow()

const chartId = props.chartId

const { error: pxChartError, fetchById: fetchPxChart } = usePxCharts()
const {
  updateItem: updatePxChartContainer,
  createItem: createPxChartContainer,
  deleteItem: deletePxChartContainer,
} = usePxChartContainers(chartId)
const { createItem: createPxEdge, deleteItem: deletePxEdge } = usePxChartEdges(chartId)

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const edgeTypes = {
  pxGraph: markRaw(PxGraphEdge),
}

const nodeDefaultValues = {
  type: 'pxGraph',
  layout: {
    position_x: 100,
    position_y: 100,
    width: 400,
    height: 0,
  },
}

const edgeDefaultValues = {
  type: 'pxGraph',
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 20,
    height: 20,
  },
}

// Load graph with Vue Flow properties
async function loadGraph() {
  loading.value = true
  try {
    const data = await fetchPxChart(chartId)
    if (data) {
      nodes.value = data.containers.map((n: PxChartContainer) => ({
        id: n.id,
        type: nodeDefaultValues.type,
        position: {
          x: n.layout.position_x ?? nodeDefaultValues.layout.position_x,
          y: n.layout.position_y ?? nodeDefaultValues.layout.position_y,
        },
        height: n.layout.height,
        width: n.layout.width,
        data: { name: n.name, content: n.content, px_chart: n.px_chart },
      }))

      edges.value = data.edges.map((e: PxChartEdge) => ({
        id: e.id,
        source: e.source,
        sourceHandle: e.sourceHandle,
        target: e.target,
        targetHandle: e.targetHandle,
        markerEnd: edgeDefaultValues.markerEnd,
        type: edgeDefaultValues.type,
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

async function onNodeDragStop(event: NodeDragEvent) {
  try {
    const node = event.node
    await updatePxChartContainer(node.id, {
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
  const newContainerPayload = {
    id: newId,
    name: 'New container',
    content: null,
    layout: {
      position_x: position_x,
      position_y: position_y,
      width: nodeDefaultValues.layout.width,
      height: nodeDefaultValues.layout.height,
    },
  }
  try {
    await createPxChartContainer(newContainerPayload)
    nodes.value.push({
      id: newId,
      type: nodeDefaultValues.type,
      position: {
        x: newContainerPayload.layout.position_x ?? nodeDefaultValues.layout.position_x,
        y: newContainerPayload.layout.position_y ?? nodeDefaultValues.layout.position_y,
      },
      height: newContainerPayload.layout.height,
      width: newContainerPayload.layout.width,
      data: {
        name: newContainerPayload.name,
        content: newContainerPayload.content,
        px_chart: props.chartId,
      },
    })
  } catch {
    alert('Failed to add node: ' + error.value)
  }
}

function onConnect(connection: Connection) {
  if (
    connection.source == null ||
    connection.sourceHandle == null ||
    connection.target == null ||
    connection.targetHandle == null ||
    chartId == null
  ) {
    alert('onConnect did not provide enough information. Aborting!')
    return
  }

  const newUuid = v4()
  createPxEdge({
    id: newUuid,
    source: connection.source,
    sourceHandle: connection.sourceHandle!,
    target: connection.target,
    targetHandle: connection.targetHandle!,
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
        type: edgeDefaultValues.type,
        markerEnd: edgeDefaultValues.markerEnd,
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

async function handleDeletePxGraphContainer(containerId: string) {
  await deletePxChartContainer(containerId)

  nodes.value.splice(
    nodes.value.findIndex((node) => node.id === containerId),
    1,
  )

  // Remove all edges connected to removed container from local model
  edges.value = edges.value.filter(
    (edge) => edge.source !== containerId && edge.target !== containerId,
  )
}

async function handleUpdatePxGraphContainer(updatedPxChartContainer: Partial<PxChartContainer>) {
  if (!updatedPxChartContainer.id) {
    alert('An update was issued to a container, however, no ID was provided. Aborting.')
    return
  }

  // Here, we have to make sure that properties like name, content, or pxgraph are handled correctly
  // This means, that for the backend, the updatedPxChartContainer can just be used, however, for
  // frontend array, these attributes need to be put into data.
  let data = null
  if (updatedPxChartContainer.content !== undefined) {
    data = merge(data, { data: { content: updatedPxChartContainer.content } })
  }
  if (updatedPxChartContainer.name) {
    data = merge(data, { data: { name: updatedPxChartContainer.name } })
  }
  if (updatedPxChartContainer.px_chart) {
    data = merge(data, { data: { px_chart: updatedPxChartContainer.px_chart } })
  }

  // Update container in backend
  await updatePxChartContainer(updatedPxChartContainer.id!, updatedPxChartContainer)

  nodes.value.splice(
    nodes.value.findIndex((node) => node.id === updatedPxChartContainer.id),
    1,
    merge(
      nodes.value[nodes.value.findIndex((node) => node.id === updatedPxChartContainer.id)],
      updatedPxChartContainer,
      data,
    ),
  )
}

async function handleAddPxNode(pxGraphContainerId: string, pxNodeId: string) {
  const updatedPxGraphContainerContent = {
    id: pxGraphContainerId,
    content: pxNodeId,
  }

  await handleUpdatePxGraphContainer(updatedPxGraphContainerContent)
}

async function handleDeletePxNode(pxGraphContainerId: string) {
  const updatedPxGraphContainerContent = {
    id: pxGraphContainerId,
    content: null,
  }

  await handleUpdatePxGraphContainer(updatedPxGraphContainerContent)
}

async function onNodesChange(changes: NodeChange[]) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxChartContainer(change.id)
    }
  }
}

async function onEdgesChange(changes: EdgeChange[]) {
  for (const change of changes) {
    if (change.type === 'remove') {
      await deletePxEdge(change.id)
    }
  }
}

function onContextMenu(mouseEvent: MouseEvent) {
  // prevent the browser's default menu
  mouseEvent.preventDefault()
  // for now, just create a container
  const pos = screenToFlowCoordinate({ x: mouseEvent.x, y: mouseEvent.y })
  addNode(pos.x, pos.y)
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
        <UButton size="xl" icon="i-lucide-plus" color="primary" @click="addNode(0, 0)" />
      </UTooltip>
    </Panel>
  </VueFlow>

  <div v-if="error" style="color: red; margin-top: 1rem">
    {{ error }}
  </div>
</template>

<style scoped></style>
