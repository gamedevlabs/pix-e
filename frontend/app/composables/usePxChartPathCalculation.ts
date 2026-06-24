import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

import {
  type PxKeySet,
  getKeySetFromKeyAssignment,
  mergePxKeySets,
  pxKeyInventoriesAreEqual,
  pxKeySetsAreEqual,
  filterPxKeySet,
} from '~/utils/pxkeysets'

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

  const fixedPxKeyDefinitions = computed(() => {
    return pxKeyDefinitions.value.filter((def) => def.fixed)
  })

  interface QueueNode {
    id: string
    prio: number
    keys: PxKeySet[]
    name: string
    alreadyUnlocked: string[]
    alreadyCollected: string[]
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

    //const qNodeIdsToNodeIds: Record<number, string> = {}

    //let qNodeCount = 1
    const firstNodeKeys = getKeySetFromKeyAssignment(getKeysInNode(sourceId))
    const firstNodeInventory = initialInventory.map((keyset) =>
      mergePxKeySets(keyset, firstNodeKeys),
    )
    const q: QueueNode[] = [
      {
        id: sourceId,
        prio: 0,
        keys: firstNodeInventory,
        name: nodes.value.filter((node) => node.id === sourceId)[0].data.name,
        alreadyUnlocked: [],
        alreadyCollected: Object.keys(firstNodeKeys).length > 0 ? [sourceId] : [],
      },
    ]
    //qNodeIdsToNodeIds[qNodeCount++] = sourceId
    const dist = new Map<string, number>()
    const prev = new Map<string, string>()
    const prevEdges = new Map<string, Edge>()
    const states = new Map<string, QueueNode>()

    const sourceNodeStateKey = makeStateKey(q[0])
    dist.set(sourceNodeStateKey, 0)
    states.set(sourceNodeStateKey, q[0])

    /*for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(qNodeCount, Infinity)
        q.push({
          qId: qNodeCount,
          id: node.id,
          prio: Infinity,
          keys: [getKeySetFromKeyAssignment(node.data.keys)],
          name: node.data.name,
          revisit: false,
          alreadyUnlocked: [],
        })
        qNodeIdsToNodeIds[qNodeCount++] = node.id
      }
    }*/

    console.log(`initial q: ${JSON.stringify(q, null, 2)}`)

    // sort (descending so we can use pop)
    q.sort((n1, n2) => n2.prio - n1.prio)

    // iterate
    let found = false
    //let inventory: PxKeySet[] = []
    const allLockedEdges: string[] = []

    // with backtracking, nodes are considered to exist in different realities where different keysets may be available
    // this Record tracks which nodes have been visited with which inventories (a.k.a. in which realities)
    //const nodesVisitedWithKeys: Record<string, PxKeySet[][]> = {}

    //let targetQId: number | undefined = 0
    let targetKeyState: string = ''

    while (q.length && !found) {
      const poppedNodeState = q.pop()
      if (!poppedNodeState) {
        break
      }

      if (poppedNodeState.id === targetId) {
        console.log(`Found target node!`)
        found = true
        targetKeyState = makeStateKey(poppedNodeState)
        //targetQId = outNodeQId
        //previousInventory.value = q.find((entry) => entry.id === edgeTarget)!.keys
        break
      }

      // console.log(`Processing node: ${JSON.stringify(node, null, 2)}`)

      /*if (!nodesVisitedWithKeys[node.id]) {
        nodesVisitedWithKeys[node.id] = [node.keys]
      } else if (
        nodesVisitedWithKeys[node.id]!.every((inv) => !pxKeyInventoriesAreEqual(inv, node.keys))
      ) {
        nodesVisitedWithKeys[node.id]!.push(node.keys)
      }*/

      const outEdges = getConnectedEdges(poppedNodeState.id, edges.value).filter(
        (edge) => edge.source === poppedNodeState.id || edge.data.bidirectional,
      )

      /*if (useLocks) {
        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = outEdges.reduce(
          (acc, edge) =>
            node.alreadyUnlocked.includes(edge.id) ||
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
      }*/

      console.log(`Found ${outEdges.length} outgoing Edges in node ${poppedNodeState.name}!`)

      const currentDistance = dist.get(makeStateKey(poppedNodeState))!

      const keySet = getKeySetFromKeyAssignment(getKeysInNode(poppedNodeState.id))

      if (
        Object.keys(keySet).length > 0 &&
        !poppedNodeState.alreadyCollected.includes(poppedNodeState.id)
      ) {
        console.log('new key set!')

        const currentInventory = [...poppedNodeState.keys]
        const unlockedEdges = [...poppedNodeState.alreadyUnlocked]

        const newNodeState = {
          id: poppedNodeState.id,
          prio: currentDistance,
          keys: currentInventory.map((keyset) => mergePxKeySets(keyset, keySet)),
          name: poppedNodeState.name,
          alreadyUnlocked: [...unlockedEdges],
          alreadyCollected: [...poppedNodeState.alreadyCollected, poppedNodeState.id],
        }

        const newStateKey = makeStateKey(newNodeState)

        const oldDist = dist.get(newStateKey) ?? Infinity

        if (currentDistance < oldDist) {
          dist.set(newStateKey, currentDistance)
          states.set(newStateKey, newNodeState)

          prev.set(newStateKey, makeStateKey(poppedNodeState))
          //prevEdges.set(newStateKey, prevEdges.get(makeStateKey(poppedNodeState))!)

          q.push(newNodeState)
        }
      }

      // check each outgoing edge
      for (const outEdge of outEdges) {
        // console.log(`Checking outgoing edge to ${outEdge.target !== node.id ? outEdge.target : outEdge.source}`)

        // Get Edge Target
        const edgeTarget =
          !outEdge.data.bidirectional || outEdge.source === poppedNodeState.id
            ? outEdge.target
            : outEdge.source
        const edgeTargetName = nodes.value.filter((node) => node.id === edgeTarget)[0].data.name

        let currentInventory = [...poppedNodeState.keys]
        let unlockedEdges = [...poppedNodeState.alreadyUnlocked]

        // Check whether edge is unlocked or needs to be unlocked
        if (
          useLocks &&
          outEdge.data.locks.length != 0 &&
          !poppedNodeState.alreadyUnlocked.includes(outEdge.id)
        ) {
          console.log('LOCKety: outgoing edge is locked')
          // If it needs to be unlocked, check with how many keys

          console.log(`LOCKety current ${JSON.stringify(canonicalizeInventory(currentInventory))}`)
          if (currentInventory.some((keys) => canUnlock(keys, outEdge.data.locks))) {
            // Nice, add an unlocked alternative
            // one for each key??

            // Check whether it is permanent/reversible/etc.
            unlockedEdges = [...poppedNodeState.alreadyUnlocked, outEdge.id]

            console.log('LOCKety: can we ever unlock this bitch')

            if (!settings.value.ignore_consumable_keys) {
              console.log(
                `consumable: currently in node ${poppedNodeState.name} with ${JSON.stringify(canonicalizeInventory(currentInventory))} for ${edgeTargetName}`,
              )

              // console.log(`Updating inventory for ${outNodeQId} from ${node.qId}`)
              // console.log(`inventory: ${JSON.stringify(inventory, null, 2)}`)
              let inventoryAfterConsumption: PxKeySet[] = removeConsumed(
                currentInventory,
                outEdge.data.locks,
              )

              const possibleInventoriesAfterUnlock = currentInventory
                .filter((keyset) => canUnlock(keyset, outEdge.data.locks))
                .flatMap((keyset) => removeConsumed([keyset], outEdge.data.locks))

              possibleInventoriesAfterUnlock.forEach((keySet) => {
                console.log(`consumable: keyset ${JSON.stringify(keySet)} unlocked`)
              })

              console.log(
                `consumable after ${JSON.stringify(canonicalizeInventory(inventoryAfterConsumption))}`,
              )

              // a potential softlock occurs when unlock is possible with some, but not all keysets in inventory
              // this must be checked before removing fully consumed keysets
              if (inventoryAfterConsumption.length !== currentInventory.length) {
                result.value.softLocked.push(edgeTarget)
              }
              inventoryAfterConsumption = inventoryAfterConsumption.filter(
                (keyset) => Object.entries(keyset).length > 0,
              )
              if (!inventoryAfterConsumption.length) {
                inventoryAfterConsumption = [{}]
              }

              currentInventory = inventoryAfterConsumption
            }
          } else {
            // We don't have a key yet, so add it to unlocked edges for highlighting and filter later
            allLockedEdges.push(outEdge.id)
            continue
          }
        }
        const distanceToTarget = currentDistance + 1

        const newNodeState = {
          id: edgeTarget,
          prio: distanceToTarget,
          keys: currentInventory,
          name: nodes.value.filter((node) => node.id === edgeTarget)[0].data.name,
          alreadyUnlocked: unlockedEdges,
          alreadyCollected: [...poppedNodeState.alreadyCollected],
        }

        console.log(`old node state ${makeStateKey(poppedNodeState)}`)
        console.log(`new node state ${makeStateKey(newNodeState)}`)

        const newStateKey = makeStateKey(newNodeState)

        const oldDist = dist.get(newStateKey) ?? Infinity

        if (distanceToTarget < oldDist) {
          dist.set(newStateKey, newNodeState.prio)
          states.set(newStateKey, newNodeState)

          prev.set(newStateKey, makeStateKey(poppedNodeState))
          prevEdges.set(newStateKey, outEdge)

          q.push(newNodeState)
        }

        //const nodeState =
        //console.log(`new node state ${edgeTarget} ${distanceToTarget} ${currentInventory} ${unlockedEdges}`)

        // first check whether node is both in queue and reachable from the current state
        // (re-visited nodes hold no keys, so if a node is re-visited, all keys available in it must be available in its predecessor)
        /*let outNodeQId = q.find(
          (qNode) =>
            qNode.id === edgeTarget &&
            (pxKeyInventoriesAreEqual(currentInventory, qNode.keys)),
        )?.qId*/

        // to enable re-visiting of nodes:
        //      if successor node is not in queue (i.e. will not be processed again by regular iteration),
        //      and the target node has neither been visited LIMIT times not visited with the current inventory available,
        //      add it to queue
        /*if (
          !outNodeQId &&
          (!nodesVisitedWithKeys[edgeTarget] ||
            (nodesVisitedWithKeys[edgeTarget].length < CYCLE_LIMIT &&
              !nodesVisitedWithKeys[edgeTarget]?.some((inv) =>
                pxKeyInventoriesAreEqual(inventory, inv),
              )))
        ) {
          // console.log(`Adding for re-visit: ${getNodeName(outNodeId)} with prio ${alt} and qID ${qNodeCount}`)
          dist.set(qNodeCount, Infinity)
          q.push({
            qId: qNodeCount,
            id: edgeTarget,
            prio: distanceToTarget,
            keys: [
              filterPxKeySet(
                getKeySetFromKeyAssignment(getKeysInNode(edgeTarget)),
                fixedPxKeyDefinitions.value,
              ),
            ],
            name: node.name + " with new keys",
            alreadyUnlocked: [],
          })
          outNodeQId = qNodeCount
          qNodeIdsToNodeIds[qNodeCount++] = edgeTarget
        }*/

        // nodes may be reachable with shorter paths, but going the shorter path may miss keys that need to be collected
        // thus, we loosen the condition here to include all reachable nodes
        // potential improvement: make condition more robust by calculating combined score of dist, keys collected, ...
        /*if (outNodeQId && distanceToTarget < Infinity) {
        prev.set(outNodeQId, poppedNodeState.qId)
        prevEdges.set(outNodeQId, outEdge)
        dist.set(outNodeQId, distanceToTarget)
        const idx = findIndex(q, ['qId', outNodeQId])
        q[idx]!.prio = distanceToTarget

        // update key inventory in successor node
        if (
          useLocks &&
          !settings.value.ignore_consumable_keys &&
          !poppedNodeState.alreadyUnlocked.includes(outEdge.id)
        ) {
          // console.log(`Updating inventory for ${outNodeQId} from ${node.qId}`)
          // console.log(`inventory: ${JSON.stringify(inventory, null, 2)}`)
          let inventoryAfterConsumption: PxKeySet[] = removeConsumed(
            inventory,
            outEdge.data.locks,
          )
          // a potential softlock occurs when unlock is possible with some, but not all keysets in inventory
          // this must be checked before removing fully consumed keysets
          if (inventoryAfterConsumption.length !== inventory.length)
            result.value.softLocked.push(edgeTarget)
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

          const newlyUnlocked = [...poppedNodeState.alreadyUnlocked, outEdge.id].filter(edge => !q[idx]!.alreadyUnlocked.includes(edge))
          q[idx]!.alreadyUnlocked.push(...newlyUnlocked)
          if (!q[idx]!.alreadyUnlocked.includes(outEdge.id))
            q[idx]!.alreadyUnlocked.push(outEdge.id)
        } else if (useLocks) {
          const keysetsToAdd = inventory
            .map((keyset) => mergePxKeySets(keyset, q[idx]!.keys[0]!))
            .filter((keyset) =>
              q[idx]!.keys.every(
                (inventoryKeyset) => !pxKeySetsAreEqual(keyset, inventoryKeyset),
              ),
            )
          q[idx]!.keys.push(...keysetsToAdd)

          const newlyUnlocked = [...poppedNodeState.alreadyUnlocked].filter(edge => !q[idx]!.alreadyUnlocked.includes(edge))
          q[idx]!.alreadyUnlocked.push(...newlyUnlocked)
          if (!q[idx]!.alreadyUnlocked.includes(outEdge.id))
            q[idx]!.alreadyUnlocked.push(outEdge.id)
        }

        q.sort((n1, n2) => n2.prio - n1.prio)
      }*/
        /*if (edgeTarget === targetId) {
          console.log(`Found target node!`)
          found = true
          targetKeyState = makeStateKey(targetId)
          //targetQId = outNodeQId
          previousInventory.value = q.find((entry) => entry.id === edgeTarget)!.keys
          break
        }*/
      }

      q.sort((n1, n2) => n2.prio - n1.prio)
    }

    /*
    console.log(`prev after calculation:`)
    for (const [key, value] of prev) {
        console.log(key, value);
    }

    console.log(`qNodeIdsToNodeIds after calculation: ${JSON.stringify(qNodeIdsToNodeIds, null, 2)}`)
    */

    const seq: string[] = []
    const seqEdges = []

    if (found && targetKeyState) {
      // construct sequence
      let current: string | undefined = targetKeyState

      while (current) {
        const state = states.get(current)

        if (!state) {
          console.warn(`Missing state for key: ${current}`)
          break
        }

        seq.push(state.id)

        const edge = prevEdges.get(current)
        if (edge) {
          seqEdges.push(edge)
        }

        current = prev.get(current)
      }
    }

    //const targetQNode = states.get(targetKeyState)
    result.value.locked = result.value.locked
      .concat(allLockedEdges)
      .filter((edge) => !states.get(targetKeyState)?.alreadyUnlocked.includes(edge))
    result.value.pathEdges = seqEdges.reverse()
    return seq.reverse()
  }

  function makeStateKey(qNode: QueueNode): string {
    return JSON.stringify({
      id: qNode.id,
      keys: canonicalizeInventory(qNode.keys),
      unlocked: [...new Set(qNode.alreadyUnlocked)].sort(),
      collected: [...new Set(qNode.alreadyCollected)].sort(),
    })
  }

  function canonicalizeInventory(inventory: PxKeySet[]) {
    return inventory
      .map(canonicalizeKeySet)
      .sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))
  }

  function canonicalizeKeySet(keyset: PxKeySet): PxKeySet {
    return Object.fromEntries(
      Object.entries(keyset)
        .filter(([, count]) => count > 0)
        .sort(([a], [b]) => a.localeCompare(b)),
    )
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
