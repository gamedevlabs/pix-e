import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

import { type PxKeySet, getKeySetFromKeyAssignment, mergePxKeySets } from '~/utils/pxkeysets'

import type { PxChartPathCalculationResult } from '#imports'

export function usePxChartPathCalculation(
  nodes: Ref<Node[]>,
  edges: Ref<Edge[]>,
  settings: Ref<PxChartSettings>,
) {
  const { info: infoToast } = usePixeToast()
  const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()
  const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

  const selectedNodes = ref<string[]>([])

  const result = ref<PxChartPathCalculationResult>({
    pathNodes: [],
    pathEdges: [],
    locked: [],
    softLocked: [],
  })

  const { updateNodeStyling, updateEdgeStyling } = usePxChartPathStyling(
    nodes,
    edges,
    selectedNodes,
    settings,
    result,
    pxLockDefinitions,
    pxKeyDefinitions,
  )

  const { canUnlock, removeConsumed, pxKeyDefinitionsById, getKeysInNode } =
    usePxChartPathCalculationUnlock(nodes, settings, pxLockDefinitions, pxKeyDefinitions)

  interface QueueNode {
    id: string
    prio: number
    keys: PxKeySet[]
  }

  async function dijkstraInChart(sourceId: string, targetId: string, useLocks: boolean = true) {
    // initialize
    if (useLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const q: QueueNode[] = [
      { id: sourceId, prio: 0, keys: [getKeySetFromKeyAssignment(getKeysInNode(sourceId))] },
    ]
    const dist = new Map<string, number>()
    dist.set(sourceId, 0)
    const prev = new Map<string, string>()
    const prevEdges = new Map<string, Edge>()

    for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(node.id, Infinity)
        q.push({ id: node.id, prio: Infinity, keys: [getKeySetFromKeyAssignment(node.data.keys)] })
      }
    }

    // sort (descending so we can use pop)
    q.sort((n1, n2) => n2.prio - n1.prio)

    console.log(`Queue: ${JSON.stringify(q)}`)

    // iterate
    let found = false
    let inventory: PxKeySet[] = []
    let allLockedEdges: string[] = []
    while (q.length && !found) {
      const node = q.pop()
      if (!node) {
        break
      }

      console.log(`Node Id: ${node.id}, Inventory: ${JSON.stringify(node.keys)}`)

      let outEdges = getConnectedEdges(node.id, edges.value).filter(
        (edge) => edge.source === node.id,
      )

      if (useLocks) {
        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = outEdges.reduce(
          (acc, edge) =>
            node.keys.some((keys) => canUnlock(keys, edge.data.locks))
              ? (acc[0].push(edge), acc)
              : (acc[1].push(edge), acc),
          [[], []] as [Edge[], Edge[]],
        )

        allLockedEdges = allLockedEdges.concat(lockedOutEdges.map((edge) => edge.id))
        outEdges = unlockedOutEdges

        // clean up inventory
        inventory = node.keys.map((keyset) =>
          Object.fromEntries(
            Object.entries(keyset).filter(
              ([keyDef, _count]) => !pxKeyDefinitionsById.value[keyDef]!.fixed,
            ),
          ),
        )
      }

      for (const outEdge of outEdges) {
        const outNodeId = outEdge.target
        const alt = dist.get(node.id)! + 1
        if (alt < dist.get(outNodeId)!) {
          prev.set(outNodeId, node.id)
          prevEdges.set(outNodeId, outEdge)
          dist.set(outNodeId, alt)
          const idx = findIndex(q, ['id', outNodeId])
          q[idx]!.prio = alt

          // update key inventory in successor node
          if (useLocks && !settings.value.ignore_consumable_keys) {
            let inventoryAfterConsumption: PxKeySet[] = removeConsumed(
              inventory,
              outEdge.data.locks,
            )
            // a potential softlock occurs when unlock is possible with some, but not all keysets in inventory
            // this must be checked before removing fully consumed keysets
            if (inventoryAfterConsumption.length !== inventory.length)
              //softLocked.value.push(outNodeId)
              result.value.softLocked.push(outNodeId)
            inventoryAfterConsumption = inventoryAfterConsumption.filter(
              (keyset) => Object.entries(keyset).length > 0,
            )
            if (!inventoryAfterConsumption.length) inventoryAfterConsumption = [{}]

            // unprocessed nodes only have one keyset, so we can just index into the array
            q[idx]!.keys = inventoryAfterConsumption.map((keyset) =>
              mergePxKeySets(keyset, q[idx]!.keys[0]!),
            )
          } else if (useLocks && settings.value.ignore_consumable_keys) {
            q[idx]!.keys = inventory.map((keyset) => mergePxKeySets(keyset, q[idx]!.keys[0]!))
          }

          q.sort((n1, n2) => n2.prio - n1.prio)
        }
        if (outNodeId == targetId) {
          found = true
          break
        }
      }
    }

    const seq = []
    const seqEdges = []
    if (found) {
      // construct sequence
      let current = targetId
      if (prev.has(current) || current == sourceId) {
        while (current) {
          seq.push(current)
          if (prevEdges.has(current)) {
            seqEdges.push(prevEdges.get(current)!)
          }
          current = prev.get(current)!
        }
      }
    }

    result.value.locked = result.value.locked.concat(allLockedEdges)
    result.value.pathEdges = seqEdges.reverse()
    console.log(`pathEdges: ${result.value.pathEdges.toString()}`)
    return seq.reverse()
  }

  async function dijkstraInChartMultiple(selected: string[], useLocks: boolean = true) {
    let fullPath: string[] = []

    if (selected.length < 2) {
      return []
    }

    fullPath.push(selected[0]!)

    for (let i = 0; i < selected.length - 1; i++) {
      const nextSeq = await dijkstraInChart(selected[i]!, selected[i + 1]!, useLocks)
      if (!nextSeq.length) {
        return []
      }
      fullPath = fullPath.concat(nextSeq.slice(1))
    }

    return fullPath
  }

  async function calculatePathFromSelection(selected: string[]) {
    console.log(`Starting path calculation...`)
    console.log(`Used settings: ${JSON.stringify(settings.value)}`)
    console.log(`Found ${nodes.value.length} nodes.`)
    console.log(`Input (length ${selected.length}): ${selected.toString()}`)
    selectedNodes.value = selected
    let newPath: string[] = []
    if (selected.length == 2 && selected[0] && selected[1]) {
      newPath = await dijkstraInChart(selected[0], selected[1], settings.value.use_locks)
      if (!newPath.length) {
        newPath = await dijkstraInChart(selected[1], selected[0], settings.value.use_locks)
      }
    } else {
      newPath = await dijkstraInChartMultiple(selected, settings.value.use_locks)
    }

    if (!newPath.length) {
      infoToast('Could not calculate path between selected nodes.')
    }
    result.value.pathNodes = newPath
    console.log(
      `Finished path calculation!\nResult (length ${result.value.pathNodes.length}): ${JSON.stringify(result.value)}`,
    )
  }

  async function resetPathCalculation() {
    // reset path itself and locked edges
    result.value = {
      pathNodes: [],
      pathEdges: [],
      locked: [],
      softLocked: [],
    }
    selectedNodes.value = []
  }

  return {
    result,
    calculatePathFromSelection,
    resetPathCalculation,
    updateNodeStyling,
    updateEdgeStyling,
  }
}
