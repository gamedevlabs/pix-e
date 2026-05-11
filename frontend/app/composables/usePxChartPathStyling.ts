import type { Edge, Node } from '@vue-flow/core'

export function usePxChartPathStyling(
  nodes: Ref<Node[]>,
  edges: Ref<Edge[]>,
  selectedNodes: Ref<string[]>,
  settings: Ref<PxChartSettings>,
  result: Ref<PxChartPathCalculationResult>,
  pxLockDefinitions: Ref<PxLockDefinition[]>,
  pxKeyDefinitions: Ref<PxKeyDefinition[]>,
) {
  const { gatedPath } = usePxChartPathCalculationResult(nodes, edges, settings, pxLockDefinitions, pxKeyDefinitions, result)

  function getPathStyle(color: string) {
    return {
      border: `3px solid ${color}`,
      borderRadius: '10px',
      boxShadow: `0 0 10px ${color}`,
    }
  }

  async function updateNodeStyling() {
    // set style of nodes in calculated path
    for (const node of nodes.value) {
      if (!result.value.pathNodes.length && selectedNodes.value.includes(node.id)) {
        // use error color for selected nodes when no path connects them
        node.style = getPathStyle('var(--ui-error)')
      } else if (settings.value.show_soft_locks && result.value.softLocked.includes(node.id)) {
        // use info color for nodes with potential soft locks
        node.style = getPathStyle('var(--ui-info)')
      } else if (settings.value.use_locks && gatedPath.value.nodes.includes(node.id)) {
        // use warn color for path parts behind a soft gate
        node.style = getPathStyle('var(--ui-warning)')
      } else if (result.value.pathNodes.includes(node.id)) {
        // use primary color for nodes in regular path
        node.style = getPathStyle('var(--ui-primary)')
      } else {
        node.style = undefined
      }
    }
  }

  async function updateEdgeStyling() {
    const lockedStyle = { stroke: 'var(--ui-error)' }
    const defaultPathStyle = { stroke: 'var(--ui-primary)' }
    const softGatedPathStyle = { stroke: 'var(--ui-warning)' }

    for (const edge of edges.value) {
      if (!result.value.pathNodes.length && settings.value.use_locks && result.value.locked.includes(edge.id)) {
        edge.style = lockedStyle
      } else if (settings.value.use_locks && gatedPath.value.edges.includes(edge)) {
        edge.style = softGatedPathStyle
      } else if (result.value.pathEdges.includes(edge)) {
        edge.style = defaultPathStyle
      } else {
        edge.style = undefined
      }
    }
  }

  return {
    updateNodeStyling,
    updateEdgeStyling,
  }
}
