import type { Connection, Edge, EdgeChange, Node, NodeChange } from '@vue-flow/core'
import { useVueFlow, MarkerType } from '@vue-flow/core'
import merge from 'lodash.merge'
import { PxChartContainerAddPxNodeForm, PxChartContainerCreatePxNodeForm } from '#components'

export function usePxChartsCanvasApi(chartId: string) {
  const nodes = ref<Node[]>([])
  const edges = ref<Edge[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const path = ref<string[]>([])

  const { error: pxChartError, fetchById: fetchPxChart } = usePxCharts()
  const {
    updateItem: updatePxChartContainer,
    createItem: createPxChartContainer,
    deleteItem: deletePxChartContainer,
  } = usePxChartContainers(chartId)
  const { createItem: createPxEdge, deleteItem: deletePxEdge, updateItem: updatePxEdge } = usePxChartEdges(chartId)
  const { fetchById: fetchPxNode, fetchAll: fetchPxNodes, items: _pxNodes } = usePxNodes()
  const { fetchAll: fetchPxLocks, items: pxLocks } = usePxLocks(chartId)
  const { fetchAll: fetchPxKeys, items: pxKeys } = usePxKeys()

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

  const overlay = useOverlay()
  const modalAddPxNode = overlay.create(PxChartContainerAddPxNodeForm)
  const modalCreatePxNode = overlay.create(PxChartContainerCreatePxNodeForm)

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

    await fetchPxLocks()
    await fetchPxNodes()
    await fetchPxKeys()

    nodes.value = data.containers.map((n: PxChartContainer) => ({
      id: n.id,
      type: n.content ? 'pxNode' : containerDefaultValues.type,
      position: {
        x: n.layout.position_x ?? containerDefaultValues.layout.position_x,
        y: n.layout.position_y ?? containerDefaultValues.layout.position_y,
      },
      height: n.layout.height,
      width: n.layout.width,
      data: {
        name: n.name,
        content: n.content,
        px_chart: n.px_chart,
        keys: pxKeys.value.filter((key) => key.node === n.content),
      },
    }))

    edges.value = data.edges.map((e: PxChartEdge) => ({
      id: e.id,
      source: e.source,
      sourceHandle: e.sourceHandle,
      target: e.target,
      targetHandle: e.targetHandle,
      markerEnd: e.bidirectional ? undefined : edgeDefaultValues.markerEnd,
      type: edgeDefaultValues.type,
      data: {
        px_chart: chartId,
        locks: pxLocks.value.filter((lock) => lock.edge === e.id),
        bidirectional: e.bidirectional,
      },
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

  async function getKeysForNode(nodeId: string | null): Promise<PxKey[]> {
    if (!nodeId) {
      return []
    }
    let node
    try {
      node = await fetchPxNode(nodeId)
    } catch (err) {
      alert('Failed to fetch PxNode: ' + err.message)
      error.value = 'Failed to fetch PxNode'
      return []
    }
    if (!node) {
      alert('Failed to fetch PxNode')
      error.value = 'Failed to fetch PxNode'
      return []
    }
    return node.keys
  }

  async function getLocksForEdge(edgeId: string | null): Promise<PxLock[]> {
    if (!edgeId) {
      return []
    }
    await fetchPxLocks()
    return pxLocks.value.filter((lock) => lock.edge === edgeId)
  }

  async function addContainer(position_x = 0, position_y = 0) {
    const newContainerPayload = {
      name: 'Empty Container',
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
        keys: [],
      },
    })
    return newId
  }

  async function addContainerWithExistingNode(position_x = 0, position_y = 0) {
    const nodeId = await modalAddPxNode.open().result
    await createContainerAndAddNode(position_x, position_y, nodeId)
  }

  async function addContainerWithNewNode(position_x = 0, position_y = 0) {
    const nodeId = await modalCreatePxNode.open().result
    await createContainerAndAddNode(position_x, position_y, nodeId)
  }

  async function createContainerAndAddNode(position_x = 0, position_y = 0, nodeId: string) {
    if (!nodeId) {
      return
    } else {
      const containerId = await addContainer(position_x, position_y)
      await addNodeToContainer(containerId, nodeId)
    }
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
      data = merge(data, {
        data: { content: updatedContainer.content, keys: getKeysForNode(updatedContainer.content) },
      })
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

  async function updateKeysInContainer(id: string, keys: PxKey[]) {
    const node = nodes.value.find((node) => node.id === id)
    if (node) {
      node.data.keys = keys
    } else {
      alert('Failed to update keys in container.')
      error.value = 'Failed to update keys in container'
    }
  }

  function applyDefaultNodeChanges(moveChanges: NodeChange[]) {
    applyNodeChanges(moveChanges)
  }

  async function switchNodeInContainer(pxGraphContainerId: string) {
    const newNodeId = await modalAddPxNode.open().result

    if (!newNodeId) {
      console.log('Canceled')
      return
    }
    await removeNodeFromContainer(pxGraphContainerId)
    await addNodeToContainer(pxGraphContainerId, newNodeId)

    //TODO: following code should work, but doesn't, figure out why to make make transition between node switches cleaner
    /*
    const updatedPxGraphContainerContent = {
      type: 'pxNode' as PxContainerContentType,
      id: pxGraphContainerId,
      content: newNodeId,
    }
    console.log('new node added')
      try {
        await updateContainer(updatedPxGraphContainerContent)
          console.log('container updated')
      } catch (err) {
        alert('Failed to add node to container: ' + err.message)
        error.value = 'Failed to add node to container'
          console.log('error')
      }

     */
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
        locks: [],
        bidirectional: false,
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
      data: { px_chart: chartId, locks: [], bidirectional: false },
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

  async function updateLocksOnEdge(edgeId: string) {
    const edge = edges.value.find((e) => e.id === edgeId)
    if (!edge) {
      console.warn('Could not find edge.')
    } else {
      edge.data.locks = await getLocksForEdge(edgeId)
    }
  }

  async function changeEdgeDirectionality(edgeId: string) {
    const edge = edges.value.find((e) => e.id === edgeId)
    if (!edge) {
      console.warn(`Could not find edge. (ID: ${edgeId})`)
      console.warn(`Available Edges: ${JSON.stringify(edges.value, null, 2)}`)
    } else {
      edge.data.bidirectional = !edge.data.bidirectional
      edge.markerEnd = edge.data.bidirectional ? undefined : edgeDefaultValues.markerEnd
      await updatePxEdge(edgeId, { bidirectional: edge.data.bidirectional })
    }
  }

  return {
    nodes,
    edges,
    loading,
    error,
    path,
    pxChartError,
    loadGraph,
    addContainerWithExistingNode,
    addContainerWithNewNode,
    switchNodeInContainer,
    updateContainer,
    updateKeysInContainer,
    applyDefaultNodeChanges,
    addNodeToContainer,
    deleteContainer,
    addEdge,
    applyDefaultEdgeChanges,
    deleteEdge,
    updateLocksOnEdge,
    getKeysForNode,
    changeEdgeDirectionality,
  }
}
