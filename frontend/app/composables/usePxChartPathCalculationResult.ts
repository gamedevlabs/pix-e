import type { Edge, Node } from '@vue-flow/core'

export interface PxChartPathCalculationResult {
  pathNodes: string[]
  pathEdges: Edge[]
  locked: string[]
  softLocked: string[]
}

export function usePxChartPathCalculationResult(
  nodes: Ref<Node[]>,
  edges: Ref<Edge[]>,
  settings: Ref<PxChartSettings>,
  pxLockDefinitions: Ref<PxLockDefinition[]>,
  pxKeyDefinitions: Ref<PxKeyDefinition[]>,
  result: Ref<PxChartPathCalculationResult>,
) {

  const { getKeysInNode, isSoftUnlock } = usePxChartPathCalculationUnlock(nodes, settings, pxLockDefinitions, pxKeyDefinitions)

  const pathNodesAndEdges = computed(() => {
    return Array.from(Array(result.value.pathNodes.length), (_, i) => ({
      node: result.value.pathNodes[i]!,
      edge: result.value.pathEdges[i],
    }))
  })

  const gatedPath = computed(() => {
    if (!settings.value.use_locks) return { nodes: [], edges: [] }

    let keys: PxKeySet = {}
    const gatedNodes: string[] = []
    const gatedEdges: Edge[] = []

    let softUnlock = false
    for (const step of pathNodesAndEdges.value) {
      if (softUnlock) {
        if (step.node) gatedNodes.push(step.node)
        if (step.edge) gatedEdges.push(step.edge)
      } else {
        if (step.node)
          keys = { ...keys, ...getKeySetFromKeyAssignment(getKeysInNode(step.node)), ...keys }
        if (isSoftUnlock(keys, step.edge?.data.locks)) softUnlock = true
      }
    }
    return { nodes: gatedNodes, edges: gatedEdges }
  })

  return {
    gatedPath
  }
}
