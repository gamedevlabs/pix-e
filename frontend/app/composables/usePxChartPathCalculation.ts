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

  const previousInventory = ref<PxKeySet[]>([{}])

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

  // to prevent infinite loops during pathfinding, each node can be visited at most this many times
  const CYCLE_LIMIT = 5

  function findNodeById(id: string) {
    return nodes.value.find((node) => node.id === id)
  }

  interface QueueNode {
    qId: number
    id: string
    prio: number
    keys: PxKeySet[]
    name: string
  }

  async function dijkstraInChart(
    sourceId: string,
    targetId: string,
    useLocks: boolean = true,
    initialInventory: PxKeySet[] = [{}],
  ) {
    // initialize
    if (useLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const qNodeIdsToNodeIds: Record<number, string> = {}
    // const qNodeIdsToContainerNames: Record<number, string> = {}

    let qNodeCount = 1
    const firstNodeKeys = getKeySetFromKeyAssignment(getKeysInNode(sourceId))
    const firstNodeInventory = initialInventory.map((keyset) =>
      mergePxKeySets(keyset, firstNodeKeys),
    )
    const q: QueueNode[] = [
      {
        qId: qNodeCount,
        id: sourceId,
        prio: 0,
        keys: firstNodeInventory,
        name: findNodeById(sourceId)?.data.name,
      },
    ]
    // qNodeIdsToContainerNames[qNodeCount] = findNodeById(sourceId)?.data.name
    qNodeIdsToNodeIds[qNodeCount++] = sourceId
    const dist = new Map<number, number>()
    dist.set(1, 0)
    const prev = new Map<number, number>()
    const prevEdges = new Map<number, Edge>()

    for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(qNodeCount, Infinity)
        q.push({
          qId: qNodeCount,
          id: node.id,
          prio: Infinity,
          keys: [getKeySetFromKeyAssignment(node.data.keys)],
          name: node.data.name,
        })
        // qNodeIdsToContainerNames[qNodeCount] = node.data.name
        qNodeIdsToNodeIds[qNodeCount++] = node.id
      }
    }

    //console.log(`qNodeCount after initialization: ${qNodeCount}`)
    //console.log(`qNodeIdsToNodeIds: ${JSON.stringify(qNodeIdsToNodeIds, null, 2)}`)

    // sort (descending so we can use pop)
    q.sort((n1, n2) => n2.prio - n1.prio)

    // iterate
    let found = false
    let inventory: PxKeySet[] = []
    let allLockedEdges: string[] = []

    // with backtracking, nodes are considered to exist in different realities where different keysets may be available
    // this Record tracks which nodes have been visited with which inventories (a.k.a. in which realities)
    const nodesVisitedWithKeys: Record<string, PxKeySet[][]> = {}
    const previouslyUnlockedEdges: Set<string> = new Set()

    let targetQId: number | undefined = 0

    while (q.length && !found) {
      const node = q.pop()
      if (!node) {
        break
      }

      // console.log(`Processing node: ${JSON.stringify(node, null, 2)}`)

      if (!nodesVisitedWithKeys[node.id]) {
        nodesVisitedWithKeys[node.id] = [node.keys]
      } else {
        nodesVisitedWithKeys[node.id]?.push(node.keys)
      }

      let outEdges = getConnectedEdges(node.id, edges.value).filter(
        (edge) => edge.source === node.id || edge.data.bidirectional,
      )

      if (useLocks) {
        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = outEdges.reduce(
          (acc, edge) =>
            previouslyUnlockedEdges.has(edge.id) ||
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

      // console.log(`Found ${outEdges.length} outgoing Edges!`)

      // check each outgoing edge
      for (const outEdge of outEdges) {
        // console.log(`Checking outgoing edge: ${outEdge.id} to ${findNodeById(outEdge.target !== node.id ? outEdge.target : outEdge.source)?.data.name}`)
        previouslyUnlockedEdges.add(outEdge.id)
        const outNodeId =
          !outEdge.data.bidirectional || outEdge.source === node.id
            ? outEdge.target
            : outEdge.source
        const alt = dist.get(node.qId)! + 1

        // to enable re-visiting of nodes:
        //      if successor node is not in queue (i.e. will not be processed again by regular iteration),
        //      and the target node has neither been visited LIMIT times not visited with the current inventory available,
        //      add it to queue
        let outNodeQId = q.find((qNode) => qNode.id === outNodeId)?.qId
        if (
          !outNodeQId &&
          (!nodesVisitedWithKeys[outNodeId] ||
            (nodesVisitedWithKeys[outNodeId].length < CYCLE_LIMIT &&
              !nodesVisitedWithKeys[outNodeId]?.every((inv) =>
                pxKeyInventoriesAreEqual(inventory, inv),
              )))
        ) {
          //console.log(`Adding for re-visit: ${findNodeById(outNodeId)?.data.name} with prio ${alt}`)
          dist.set(qNodeCount, Infinity)
          q.push({
            qId: qNodeCount,
            id: outNodeId,
            prio: alt,
            keys: [{}],
            name: findNodeById(outNodeId)?.data.name,
          })
          outNodeQId = qNodeCount
          // qNodeIdsToContainerNames[qNodeCount] = findNodeById(outNodeId)?.data.name
          qNodeIdsToNodeIds[qNodeCount++] = outNodeId
        }

        // nodes may be reachable with shorter paths, but going the shorter path may miss keys that need to be collected
        // thus, we loosen the condition here to include all reachable nodes
        // potential improvement: make condition more robust by calculating combined score of dist, keys collected, ...
        if (outNodeQId && alt < Infinity) {
          prev.set(outNodeQId, node.qId)
          prevEdges.set(outNodeQId, outEdge)
          dist.set(outNodeQId, alt)
          const idx = findIndex(q, ['qId', outNodeQId])
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
              result.value.softLocked.push(outNodeId)
            inventoryAfterConsumption = inventoryAfterConsumption.filter(
              (keyset) => Object.entries(keyset).length > 0,
            )
            if (!inventoryAfterConsumption.length) inventoryAfterConsumption = [{}]

            // nodes may be reached in multiple ways
            // so we leave the original keyset in the node at index 0
            // and append inventories from preceding paths after the original keyset
            const keysetsToAdd = inventoryAfterConsumption
              .map((keyset) => mergePxKeySets(keyset, q[idx]!.keys[0]!))
              .filter((keyset) =>
                q[idx]!.keys.every(
                  (inventoryKeyset) => !pxKeySetsAreEqual(keyset, inventoryKeyset),
                ),
              )
            q[idx]!.keys.push(...keysetsToAdd)
          } else if (useLocks && settings.value.ignore_consumable_keys) {
            const keysetsToAdd = inventory
              .map((keyset) => mergePxKeySets(keyset, q[idx]!.keys[0]!))
              .filter((keyset) =>
                q[idx]!.keys.every(
                  (inventoryKeyset) => !pxKeySetsAreEqual(keyset, inventoryKeyset),
                ),
              )
            q[idx]!.keys.push(...keysetsToAdd)
          }

          q.sort((n1, n2) => n2.prio - n1.prio)
        }
        if (outNodeId === targetId) {
          console.log(`Found target node!`)
          found = true
          targetQId = outNodeQId
          break
        }
      }
    }

    /*
    console.log(`prev after calculation:`)
    for (const [key, value] of prev) {
        console.log(key, value);
    }

    console.log(`qNodeIdsToNodeIds after calculation: ${JSON.stringify(qNodeIdsToNodeIds, null, 2)}`)
    console.log(`qNodeIdsToNodeNames after calculation: ${JSON.stringify(qNodeIdsToContainerNames, null, 2)}`)
    */

    const seq: string[] = []
    const seqEdges = []
    if (found && targetQId) {
      // construct sequence
      let current = targetQId
      if (prev.has(current) || qNodeIdsToNodeIds[current] === sourceId) {
        while (current) {
          seq.push(qNodeIdsToNodeIds[current]!)
          if (prevEdges.has(current)) {
            seqEdges.push(prevEdges.get(current)!)
          }
          current = prev.get(current)!
        }
      }
    }

    result.value.locked = result.value.locked.concat(allLockedEdges)
    result.value.pathEdges = seqEdges.reverse()
    return seq.reverse()
  }

  async function dijkstraInChartMultiple(selected: string[], useLocks: boolean = true) {
    let fullPath: string[] = []

    if (selected.length < 2) {
      return []
    }

    fullPath.push(selected[0]!)

    for (let i = 0; i < selected.length - 1; i++) {
      const nextSeq = await dijkstraInChart(
        selected[i]!,
        selected[i + 1]!,
        useLocks,
        previousInventory.value,
      )
      if (!nextSeq.length) {
        return []
      }
      fullPath = fullPath.concat(nextSeq.slice(1))
    }

    return fullPath
  }

  async function calculatePathFromSelection(selected: string[]) {
    console.log(`Starting path calculation...`)
    console.log(`Using settings: ${JSON.stringify(settings.value)}`)
    console.log(`Found ${nodes.value.length} nodes.`)
    console.log(`Input (length ${selected.length}): ${selected.toString()}`)
    selectedNodes.value = selected
    let newPath: string[]
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
      `Finished path calculation!\nResult (length ${result.value.pathNodes.length}): ${JSON.stringify(result.value, null, 2)}`,
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
    previousInventory.value = [{}]
  }

  return {
    result,
    calculatePathFromSelection,
    resetPathCalculation,
    updateNodeStyling,
    updateEdgeStyling,
  }
}
