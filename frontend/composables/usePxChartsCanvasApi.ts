import type { Connection, Edge, EdgeChange, Node, NodeChange } from '@vue-flow/core'
import { useVueFlow, MarkerType } from '@vue-flow/core'
import merge from 'lodash.merge'

export function usePxChartsCanvasApi(chartId: string) {
  const nodes = ref<Node[]>([])
  const edges = ref<Edge[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const { error: pxChartError, fetchById: fetchPxChart } = usePxCharts()
  const {
    updateItem: updatePxChartContainer,
    createItem: createPxChartContainer,
    deleteItem: deletePxChartContainer,
  } = usePxChartContainers(chartId)
  const { createItem: createPxEdge, deleteItem: deletePxEdge } = usePxChartEdges(chartId)

  const { applyNodeChanges, applyEdgeChanges } = useVueFlow()

  const containerDefaultValues = {
    type: 'pxEmpty',
    name: 'New Container',
    content: null,
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

    let data

    try {
      data = await fetchPxChart(chartId)
    } catch (err) {
      alert('Could not load graph: ' + err.message)
      error.value = 'Could not load graph'
    } finally {
      loading.value = false
    }

    if (!data) {
      alert('Loaded graph has no content. Aborting...')
      error.value = 'Loaded graph is null'
      return
    }

    nodes.value = data.containers.map((n: PxChartContainer) => ({
      id: n.id,
      type: n.content ? 'pxNode' : containerDefaultValues.type,
      position: {
        x: n.layout.position_x ?? containerDefaultValues.layout.position_x,
        y: n.layout.position_y ?? containerDefaultValues.layout.position_y,
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

  /*
  async function layoutGraph(direction: string) {
    nodes.value = layout(nodes.value, edges.value, direction)

    await nextTick(() => {
      fitView()
    })
  }
   */

  async function addContainer(position_x = 0, position_y = 0) {

    const newContainerPayload = {
      name: containerDefaultValues.name,
      content: containerDefaultValues.content,
      layout: {
        position_x: position_x,
        position_y: position_y,
        width: containerDefaultValues.layout.width,
        height: containerDefaultValues.layout.height,
      },
    }

    let newId
    try {
      newId = await createPxChartContainer(newContainerPayload)
    } catch (err) {
      alert('Failed to add container: ' + err.message)
      error.value = 'Failed to add container'
    }

    nodes.value.push({
      id: newId,
      type: containerDefaultValues.type,
      position: {
        x: newContainerPayload.layout.position_x ?? containerDefaultValues.layout.position_x,
        y: newContainerPayload.layout.position_y ?? containerDefaultValues.layout.position_y,
      },
      height: newContainerPayload.layout.height,
      width: newContainerPayload.layout.width,
      data: {
        name: newContainerPayload.name,
        content: newContainerPayload.content,
        px_chart: chartId,
      },
    })
  }

  async function updateContainer(updatedContainer: Partial<PxChartContainer>) {
    if (!updatedContainer.id) {
      alert('An update was issued to a container, however, no ID was provided. Aborting.')
      error.value = 'Failed to update container due to missing ID'
      return
    }

    // Here, we have to make sure that properties like name, content, or pxgraph are handled correctly
    // This means, that for the backend, the updatedPxChartContainer can just be used, however, for
    // frontend array, these attributes need to be put into data.
    let data = null
    if (updatedContainer.content !== undefined) {
      data = merge(data, { data: { content: updatedContainer.content } })
    }
    if (updatedContainer.name) {
      data = merge(data, { data: { name: updatedContainer.name } })
    }
    if (updatedContainer.px_chart) {
      data = merge(data, { data: { px_chart: updatedContainer.px_chart } })
    }

    // Update container in backend
    try {
      await updatePxChartContainer(updatedContainer.id!, updatedContainer)
    } catch (err) {
      alert('Failed to update container: ' + err.message)
      error.value = 'Failed to update container'
    }

    nodes.value.splice(
      nodes.value.findIndex((node) => node.id === updatedContainer.id),
      1,
      merge(
        nodes.value[nodes.value.findIndex((node) => node.id === updatedContainer.id)],
        updatedContainer,
        data,
      ),
    )
  }

  function applyDefaultNodeChanges(moveChanges: NodeChange[]) {
    applyNodeChanges(moveChanges)
  }

  async function addNodeToContainer(pxGraphContainerId: string, pxNodeId: string) {
    const updatedPxGraphContainerContent = {
      type: 'pxNode' as PxContainerContentType,
      id: pxGraphContainerId,
      content: pxNodeId,
    }

    try {
      await updateContainer(updatedPxGraphContainerContent)
    } catch (err) {
      alert('Failed to add node to container: ' + err.message)
      error.value = 'Failed to add node to container'
    }
  }

  async function removeNodeFromContainer(pxGraphContainerId: string) {
    const updatedPxGraphContainerContent = {
      type: 'pxEmpty' as PxContainerContentType,
      id: pxGraphContainerId,
      content: null,
    }

    try {
      await updateContainer(updatedPxGraphContainerContent)
    } catch (err) {
      alert('Failed to remove node from container: ' + err.message)
      error.value = 'Failed to remove node from container'
    }
  }

  async function deleteContainer(containerId: string, deleteConnectedEdges: boolean = false) {
    // We first need to delete edges, as otherwise Vue Flow will throw an error
    if (deleteConnectedEdges) {
      // Delete edges in front- and backend that were connected to the deleted container
      const edgesToDelete = edges.value.filter(
        (edge) => edge.source === containerId || edge.target === containerId,
      )
      for (const edge of edgesToDelete) {
        await deleteEdge(edge.id)
      }
    }

    try {
      await deletePxChartContainer(containerId)
    } catch (err) {
      alert('Failed to delete container' + err.message)
      error.value = 'Failed to delete container'
    }

    const nodeIndexToDelete = nodes.value.findIndex((node) => node.id === containerId)
    if (nodeIndexToDelete === -1) {
      console.warn('Container was already deleted. Skipping... ' + containerId)
    } else {
      nodes.value.splice(nodeIndexToDelete, 1)
    }
  }

  async function addEdge(connection: Connection) {
    if (
      connection.source == null ||
      connection.sourceHandle == null ||
      connection.target == null ||
      connection.targetHandle == null ||
      chartId == null
    ) {
      alert('Information provided for adding an edge not complete. Aborting!')
      error.value = 'Failed to add edge due to insufficient information'
      return
    }

    let newUuid
    try {
      newUuid = await createPxEdge({
        source: connection.source,
        sourceHandle: connection.sourceHandle!,
        target: connection.target,
        targetHandle: connection.targetHandle!,
        px_chart: chartId,
      })
    } catch (err) {
      alert('Could not add edge: ' + err.message)
      error.value = 'Failed to add edge'
    }

    edges.value.push({
      id: newUuid,
      source: connection.source,
      sourceHandle: connection.sourceHandle,
      target: connection.target,
      targetHandle: connection.targetHandle,
      type: edgeDefaultValues.type,
      markerEnd: edgeDefaultValues.markerEnd,
    })
  }

  function applyDefaultEdgeChanges(moveChanges: EdgeChange[]) {
    applyEdgeChanges(moveChanges)
  }

  async function deleteEdge(edgeId: string) {
    const edgeIndexToDelete = edges.value.findIndex((edge) => edge.id === edgeId)
    if (edgeIndexToDelete === -1) {
      console.warn('Edge was already deleted. Skipping... ' + edgeId)
    } else {
      edges.value.splice(edgeIndexToDelete, 1)
    }

    try {
      await deletePxEdge(edgeId)
    } catch (err) {
      alert('Failed to delete edge' + err.message)
      error.value = 'Failed to delete edge'
    }
  }

  return {
    nodes,
    edges,
    loading,
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
  }
}
