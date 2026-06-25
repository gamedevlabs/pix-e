import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges } from '@vue-flow/core'

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

  const previousInventory = ref<PxKeySet>({})

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

  function findNodeById(id: string) {
    return nodes.value.find((node) => node.id === id)
  }

  interface QueueNode {
    id: string
    prio: number
    keys: PxKeySet
    name: string
    alreadyUnlocked: string[]
    alreadyCollected: string[]
  }

  async function dijkstraInChart(
    sourceId: string,
    targetId: string,
    useLocks: boolean = true,
    initialInventory: PxKeySet = {},
  ) {
    // initialize
    if (useLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const firstQNode = {
      id: sourceId,
      prio: 0,
      keys: initialInventory,
      name: findNodeById(sourceId)?.data.name ?? sourceId,
      alreadyUnlocked: [],
      alreadyCollected: [],
    }

    const dist = new Map<string, number>()
    const prev = new Map<string, string>()
    const prevEdges = new Map<string, Edge>()
    const states = new Map<string, QueueNode>()

    const sourceNodeStateKey = makeStateKey(firstQNode)
    dist.set(sourceNodeStateKey, 0)
    states.set(sourceNodeStateKey, firstQNode)

    const q: QueueNode[] = [firstQNode]

    function pushIfBetter(newNodeState: QueueNode, previousState: QueueNode, edge?: Edge) {
      const newStateKey = makeStateKey(newNodeState)
      const previousStateKey = makeStateKey(previousState)

      const oldDist = dist.get(newStateKey) ?? Infinity

      if (newNodeState.prio < oldDist) {
        //console.log(`consumable push ${newNodeState.name} ${newStateKey} with ${newNodeState.prio}`)

        dist.set(newStateKey, newNodeState.prio)
        states.set(newStateKey, newNodeState)

        prev.set(newStateKey, previousStateKey)

        if (edge) {
          prevEdges.set(newStateKey, edge)
        }

        q.push(newNodeState)
      }
    }

    // iterate
    let found = false
    const allLockedEdges: string[] = []

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
        previousInventory.value = { ...poppedNodeState.keys }
        //console.log(`previous inventory for real ${JSON.stringify(previousInventory.value)}`)
        break
      }

      const outEdges = getConnectedEdges(poppedNodeState.id, edges.value).filter(
        (edge) => edge.source === poppedNodeState.id || edge.data.bidirectional,
      )

      //console.log(`Found ${outEdges.length} outgoing Edges in node ${poppedNodeState.name}!`)

      const currentDistance = dist.get(makeStateKey(poppedNodeState))!

      const keySet = getKeySetFromKeyAssignment(getKeysInNode(poppedNodeState.id))
      const entries = Object.entries(keySet)

      const fixedKeys = Object.fromEntries(
        entries.filter(([keyDef]) => pxKeyDefinitionsById.value[keyDef]!.fixed),
      )

      const nonFixedKeys = Object.fromEntries(
        entries.filter(([keyDef]) => !pxKeyDefinitionsById.value[keyDef]!.fixed),
      )

      if (
        Object.keys(nonFixedKeys).length > 0 &&
        !poppedNodeState.alreadyCollected.includes(poppedNodeState.id)
      ) {
        const currentInventory = { ...poppedNodeState.keys }
        const newInventory = mergePxKeySets(currentInventory, nonFixedKeys)

        /*console.log(
          `consumable: collecting new key set before ${JSON.stringify(currentInventory)} after ${JSON.stringify(newInventory)} in ${poppedNodeState.name}`,
        )*/

        const newNodeState = {
          id: poppedNodeState.id,
          prio: currentDistance,
          keys: newInventory,
          name: poppedNodeState.name,
          alreadyUnlocked: [...poppedNodeState.alreadyUnlocked],
          alreadyCollected: [...poppedNodeState.alreadyCollected, poppedNodeState.id],
        }

        pushIfBetter(newNodeState, poppedNodeState)
      }

      // check each outgoing edge
      for (const outEdge of outEdges) {
        // console.log(`Checking outgoing edge to ${outEdge.target !== node.id ? outEdge.target : outEdge.source}`)

        // Get Edge Target
        const edgeTarget =
          !outEdge.data.bidirectional || outEdge.source === poppedNodeState.id
            ? outEdge.target
            : outEdge.source

        const edgeTargetName = findNodeById(edgeTarget)?.data.name ?? edgeTarget

        const currentInventory = { ...poppedNodeState.keys }
        let possibleInventoriesAfterConsumption = [currentInventory]
        let unlockedEdges = [...poppedNodeState.alreadyUnlocked]

        /*console.log(
          `consumable: currently in node ${poppedNodeState.name} with ${JSON.stringify(canonicalizeKeySet(poppedNodeState.keys))} for ${edgeTargetName} with ${currentDistance}`,
        )*/

        // Check whether edge is unlocked or needs to be unlocked
        if (
          useLocks &&
          outEdge.data.locks.length != 0 &&
          !poppedNodeState.alreadyUnlocked.includes(outEdge.id)
        ) {
          if (canUnlock(currentInventory, outEdge.data.locks)) {
            // TODO: Check whether it is permanent/reversible/etc.
            unlockedEdges = [...poppedNodeState.alreadyUnlocked, outEdge.id]

            if (!settings.value.ignore_consumable_keys) {
              possibleInventoriesAfterConsumption = removeConsumed(
                [currentInventory],
                outEdge.data.locks,
              )

              /*console.log(
                `consumable after ${JSON.stringify(canonicalizeInventory(possibleInventoriesAfterConsumption))}`,
              )*/

              // a potential softlock occurs when unlock is possible with more than one key
              if (possibleInventoriesAfterConsumption.length > 1) {
                result.value.softLocked.push(edgeTarget)
              }
            }
          } else if (canUnlock(fixedKeys, outEdge.data.locks)) {
            unlockedEdges = [...poppedNodeState.alreadyUnlocked, outEdge.id]
          } else {
            // We don't have a key (yet), so add it to locked edges for highlighting (and filtering) later
            allLockedEdges.push(outEdge.id)
            continue
          }
        }
        const distanceToTarget = currentDistance + 1

        possibleInventoriesAfterConsumption.forEach((inventory) => {
          const newNodeState = {
            id: edgeTarget,
            prio: distanceToTarget,
            keys: inventory,
            name: edgeTargetName,
            alreadyUnlocked: unlockedEdges,
            alreadyCollected: [...poppedNodeState.alreadyCollected],
          }

          pushIfBetter(newNodeState, poppedNodeState, outEdge)

          //console.log("consumable for each inventory")

          //console.log(`old node state ${makeStateKey(poppedNodeState)}`)
          //console.log(`new node state ${makeStateKey(newNodeState)}`)
        })
      }

      // sort (descending so we can use pop)
      q.sort((n1, n2) => n2.prio - n1.prio)
    }

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

        const prevKey = prev.get(current)
        const prevState = prevKey ? states.get(prevKey) : undefined

        const isGhostConnection =
          prevState && prevState.id === state.id

        if (!isGhostConnection) {
          seq.push(state.id)

          const edge = prevEdges.get(current)
          if (edge) {
            seqEdges.push(edge)
          }
        }

        current = prevKey
      }
    }

    result.value.locked = result.value.locked
      .concat(allLockedEdges)
      .filter((edge) => !states.get(targetKeyState)?.alreadyUnlocked.includes(edge))
    result.value.pathEdges = seqEdges.reverse()
    return seq.reverse()
  }

  function makeStateKey(qNode: QueueNode): string {
    return JSON.stringify({
      id: qNode.id,
      keys: canonicalizeKeySet(qNode.keys),
      unlocked: [...new Set(qNode.alreadyUnlocked)].sort(),
      collected: [...new Set(qNode.alreadyCollected)].sort(),
    })
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
    previousInventory.value = {}
  }

  return {
    result,
    calculatePathFromSelection,
    resetPathCalculation,
    updateNodeStyling,
    updateEdgeStyling,
  }
}
