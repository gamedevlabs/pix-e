import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

export function usePxChartPathCalculation(
  nodes: Ref<Node[]>,
  edges: Ref<Edge[]>,
  settings: Ref<PxChartSettings>,
) {
  const { info: infoToast } = usePixeToast()
  const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()
  const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

  const selectedNodes = ref<string[]>([])

  const path = ref<string[]>([]) // TODO: deprecate?
  const pathEdges = ref<Edge[]>([])
  const locked = ref<string[]>([])
  const softLocked = ref<string[]>([])

  type PxKeySet = Record<string, number>

  function getKeySetFromDefArray(keys: string[]) : PxKeySet {
    if (!keys || !keys.length) return {}
    
    const keyset: PxKeySet = {}
    for (const key of keys) {
        if (!keyset[key]) keyset[key] = 0
        keyset[key] += 1
    }
    return keyset
  }

  // assumes the input is a single assignment,
  // i.e. each definition can only appear once
  function getKeySetFromKeyAssignment(keys: PxKey[]) : PxKeySet {
    if (!keys || !keys.length) return {}

    const keyset: PxKeySet = {}
    for (const key of keys) {
        keyset[key.definition] = key.count
    }
    return keyset
  }

  function pxKeySetDifference(inventory: PxKeySet, consumed: PxKeySet) : PxKeySet {
    const res = {...inventory}
    for (const [def, count] of Object.entries(consumed)) {
        if (!res[def] || res[def] < 1) {
            return {}
        } else if (pxKeyDefinitionsById.value[def]?.consumable) {
            res[def] -= count
        }
    }
    return res
  }
  
  function isSoftGate(lock: PxLock) {
    return pxLockDefinitionsById.value[lock.definition]!.soft_gate
  }

  const softGatedEdges = computed(() => {
    return edges.value.filter(edge => edge.data.locks.every((lock: PxLock) => isSoftGate(lock)))
  })

  const pathNodes = computed(() => {
    return path.value.map(nodeId => nodes.value.find(node => node.id === nodeId)!)
  })

  const pathNodesAndEdges = computed(() => {
    return Array.from(Array(pathNodes.value.length), (_, i) => ({ node: pathNodes.value[i]!, edge: pathEdges.value[i]}));
  })

  const gatedPath = computed(() => {
    let keys: PxKeySet = {}
    const gatedNodes: Node[] = []
    const gatedEdges: Edge[] = []

    if (!settings.value.use_locks) return { nodes: gatedNodes, edges: gatedEdges }

    let softUnlock = false
    for(const step of pathNodesAndEdges.value) {
        if (softUnlock) {
            if (step.node) gatedNodes.push(step.node)
            if (step.edge) gatedEdges.push(step.edge)
        } else {
            if (step.node) keys = { ...keys, ...getKeySetFromKeyAssignment(step.node.data.keys), ...keys }
            if (isSoftUnlock(keys, step.edge?.data.locks)) {
                console.log(`soft unlock found on edge ${step.edge?.id}`)
                softUnlock = true
            }
        }
    }
    return { nodes: gatedNodes, edges: gatedEdges }
  })

  const pxLockDefinitionsById: ComputedRef<Record<string, PxLockDefinition>> = computed(() => {
    return pxLockDefinitions.value.reduce((acc, def) => ({ [def.id]: def, ...acc}), {});
  })
  
  const pxKeyDefinitionsById: ComputedRef<Record<string, PxKeyDefinition>> = computed(() => {
    return pxKeyDefinitions.value.reduce((acc, def) => ({ [def.id]: def, ...acc}), {});
  })

  function getKeysInNode(nodeId: string) : PxKey[] {
    return nodes.value.find((node) => node.id === nodeId)!.data.keys
  }

  function getNode(nodeId: string) : Node {
    return nodes.value.find((node) => node.id === nodeId)!
  }

  function cartesian(sets: string[][]) {
    if (!sets.length || sets.every(set => !set.length)) {
        return [[]]
    }

    let prod: string[][] = sets[0]!.map((x) => [x])

    sets.slice(1).forEach((set) => {
      let newProd: string[][] = []
      set.forEach((element) => {
        newProd = newProd.concat(prod.map((p) => p.concat([element])))
      })
      prod = newProd
    })

    return prod
  }

  // assumes non-soft gate locks can be unlocked with available keys
  function isSoftUnlock(keys: PxKeySet, locks: PxLock[]) {
    if (!locks || !locks.length) {
      return false
    }

    const softGates : PxLock[] = locks
      .filter((lock) => pxLockDefinitionsById.value[lock.definition]!.soft_gate)

    return !canUnlock(keys, softGates, false)
  }

  function countConsumable(keys: PxKeySet) : number {
    let sum = 0
    for (const [defId, count] of Object.entries(keys)) {
        if (pxKeyDefinitionsById.value[defId]!.consumable) sum += count
    }
    return sum
  }

  // removes consumed keys for each valid combination of inventory keyset and unlocking key combination
  function removeConsumed(inventory: PxKeySet[], locks: PxLock[]) : PxKeySet[] {
    if (!locks.length) return inventory

    const consumableRequirements = locks
        .map(lock => pxLockDefinitionsById.value[lock.definition]!.unlocked_by)
        .filter(requiredKeys => requiredKeys.filter(keyDef => pxKeyDefinitionsById.value[keyDef]!.consumable).length)

    if (!consumableRequirements.length) return inventory

    const unlockingKeySets: PxKeySet[] = cartesian(consumableRequirements)
        .map(keys => getKeySetFromDefArray(keys))
    //console.log(`unlockingKeySets: ${JSON.stringify(unlockingKeySets)}`)
    //console.log(`keysInInventory: ${JSON.stringify(inventory)}`)

    let updatedKeySets: PxKeySet[] = []
    for (const keyset of inventory) {
        for (const unlocking of unlockingKeySets) {
            const canUnlock = Object.entries(unlocking)
                .every(([keyDefId, count]) => 
                    // locks can be unlocked if keys are present and, if consumable, present at least as many times as required
                    keyset[keyDefId] &&
                    (!pxKeyDefinitionsById.value[keyDefId]!.consumable || keyset[keyDefId] >= count))
            if (canUnlock) {
                // if current keyset matches unlocking configuration: add current keyset (minus required consumable keys) to new inventory
                updatedKeySets.push(pxKeySetDifference(keyset, unlocking))
            }
        }
    }
    updatedKeySets = updatedKeySets.filter(keyset => Object.entries(keyset).length > 0)
    // console.log(`updatedKeySets: ${JSON.stringify(updatedKeySets)}`)
    
    return updatedKeySets
  } 

  // removes consumed keys heuristically: chooses unlocking key combination with smallest number of consumable keys
  function _consumedKeys(keysInInventory: PxKeySet, locks: PxLock[]) : PxKeySet {
    if (!locks.length) return {}

    const consumableRequirements = locks
        .map(lock => pxLockDefinitionsById.value[lock.definition]!.unlocked_by)
        .filter(requiredKeys => requiredKeys.filter(keyDef => pxKeyDefinitionsById.value[keyDef]!.consumable).length)

    if (!consumableRequirements.length) return {}

    const unlockingKeySets: PxKeySet[] = cartesian(consumableRequirements)
        .map(keys => getKeySetFromDefArray(keys))
    console.log(`unlockingKeySets: ${JSON.stringify(unlockingKeySets)}`)
    console.log(`keysInInventory: ${JSON.stringify(keysInInventory)}`)

    const unlockedKeySets: PxKeySet[] = unlockingKeySets
        .filter((unlocking) => Object.entries(unlocking)
            .every(([keyDefId, count]) => 
                // locks can be unlocked if keys are present and, if consumable, present at least as many times as required
                keysInInventory[keyDefId] &&
                (!pxKeyDefinitionsById.value[keyDefId]!.consumable || keysInInventory[keyDefId] >= count))
        )
        .sort((ks1, ks2) => countConsumable(ks1) - countConsumable(ks2)); // heuristic to determine which keys to consume
    
    if (!unlockedKeySets.length) return {}
    
    const bestKeySet = unlockedKeySets[0]!
    
    return Object.fromEntries(Object.entries(bestKeySet).filter(([keyDef, _count]) => pxKeyDefinitionsById.value[keyDef]!.consumable))
  }

  function canUnlock(keysInInventory: PxKeySet, locks: PxLock[], unlockSoftGates: boolean = true) {
    if (!locks.length) {
      return true
    }

    // for set of locks, determine all sets of keys that can unlock them
    const requiredKeysPerLock: string[][] = locks
      .flatMap(lock => new Array(lock.count).fill([lock.definition]))
      .map((lockDefId) => pxLockDefinitionsById.value[lockDefId]!)
      .map((def) => def.soft_gate && unlockSoftGates ? [] : def.unlocked_by)
    const unlockingKeySets: PxKeySet[] = cartesian(requiredKeysPerLock)
        .map(keys => getKeySetFromDefArray(keys))

    // edge is unlockable if any unlocking key set is a subset of the available keys
    const canUnlock = unlockingKeySets.some((unlocking) =>
      Object.entries(unlocking).every(
        ([key, count]) =>
          // locks can be unlocked if keys are present and, if consumable, present at least as many times as required
          keysInInventory[key] &&
          (!pxKeyDefinitionsById.value[key]!.consumable || settings.value.ignore_consumable_keys || keysInInventory[key] >= count),
      ),
    )
    return canUnlock
  }

  interface QueueNode {
        id: string,
        prio: number,
        keys: PxKeySet[]
  }

  async function dijkstraInChart(sourceId: string, targetId: string, useLocks: boolean = true) {
    // initialize
    if (useLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const q: QueueNode[] = [{ id: sourceId, prio: 0, keys: [getKeySetFromKeyAssignment(getKeysInNode(sourceId))] }]
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
    
    // console.log(`queue: ${JSON.stringify(q)}`)

    // iterate
    let found = false
    let inventory: PxKeySet[] = []
    let allLockedEdges: string[] = []
    while (q.length && !found) {
      const node = q.pop()
      if (!node) {
        break
      }
      // console.log(`node: ${JSON.stringify(node)}`)

      let outEdges = getConnectedEdges(node.id, edges.value)
          .filter((edge) => edge.source === node.id)

      if (useLocks) {
        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = outEdges
          .reduce(
            (acc, edge) =>
              node.keys.some(keys => canUnlock(keys, edge.data.locks))
                ? (acc[0].push(edge), acc)
                : (acc[1].push(edge), acc),
            [[], []] as [Edge[], Edge[]],
          )

        allLockedEdges = allLockedEdges.concat(lockedOutEdges.map((edge) => edge.id))
        outEdges = unlockedOutEdges

        // clean up inventory
        inventory = node.keys.map(keyset => Object.fromEntries(Object.entries(keyset).filter(([keyDef, _count]) => !pxKeyDefinitionsById.value[keyDef]!.fixed)))
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

          if (useLocks && !settings.value.ignore_consumable_keys) {
            let inventoryAfterConsumption: PxKeySet[] = removeConsumed(
              inventory,
              outEdge.data.locks,
            )
            // a potential softlock occurs when unlock is possible with some, but not all keysets in inventory
            // this must be checked before removing fully consumed keysets
            if (inventoryAfterConsumption.length !== inventory.length) {
              softLocked.value.push(outNodeId)
            }
            inventoryAfterConsumption = inventoryAfterConsumption.filter(
              (keyset) => Object.entries(keyset).length > 0,
            )
            // console.log(`inventoryAfterConsumption: ${JSON.stringify(inventoryAfterConsumption)}`)

            // unprocessed nodes only have one keyset, so we can just index into the array
            q[idx]!.keys = inventoryAfterConsumption.map((keyset) => ({
              ...keyset,
              ...q[idx]!.keys[0],
            }))
          } else if (useLocks && settings.value.ignore_consumable_keys) {
            q[idx]!.keys = inventory.map((keyset) => ({
              ...keyset,
              ...q[idx]!.keys[0],
            }))
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

    locked.value = locked.value.concat(allLockedEdges)
    pathEdges.value = seqEdges.reverse()
    console.log(`pathEdges: ${pathEdges.value.toString()}`)
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
    //let newPathIgnoringLocks: string[] = []
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
    path.value = newPath
    console.log(
      `Finished path calculation!\nResult (length ${path.value.length}): ${path.value.toString()}\nLocked Edges: ${locked.value.toString()}`,
    )
  }

  async function resetPathCalculation() {
    // reset path itself and locked edges
    path.value = []
    pathEdges.value = []
    locked.value = []
    selectedNodes.value = []
    softLocked.value = []
  }

  async function updatePathHighlight() {
    const pathNodeStyle = {
      border: '3px solid var(--ui-primary)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-primary)',
    }

    // use warn color for path parts behind a soft gate
    const softGatedPathNodeStyle = {
      border: '3px solid var(--ui-warning)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-warning)',
    }

    // use error color for selected nodes when no path connects them
    const noPathNodeStyle = {
      border: '3px solid var(--ui-error)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-error)',
    }

    // set style of nodes in calculated path
    for (const node of nodes.value) {
      node.style = path.value.includes(node.id) ? pathNodeStyle : undefined
      if (!node.style && selectedNodes.value.includes(node.id)) {
        node.style = noPathNodeStyle
      }
    }
    for (const node of gatedPath.value.nodes) {
      node.style = softGatedPathNodeStyle
    }
  }

  async function updateEdgeStyling() {
    const lockedStyle = { stroke: 'var(--ui-error)' }
    const defaultPathStyle = { stroke: 'var(--ui-primary)' }
    const softGatedPathStyle = { stroke: 'var(--ui-warning)' }

    if (!path.value.length && settings.value.use_locks) {
      for (const edge of edges.value) {
        edge.style = locked.value.includes(edge.id) ? lockedStyle : undefined
      }
    } else {
      for (const edge of edges.value) {
        edge.style = pathEdges.value.includes(edge) ? defaultPathStyle : undefined
      }
      if (settings.value.use_locks) {
        for (const edge of gatedPath.value.edges) {
          edge.style = softGatedPathStyle
        }
      }
    }
  }

  return {
    path,
    calculatePathFromSelection,
    resetPathCalculation,
    updatePathHighlight,
    updateEdgeStyling,
  }
}
