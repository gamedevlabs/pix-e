import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges, getOutgoers } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

export function usePxChartPathCalculation(nodes: Ref<Node[]>, edges: Ref<Edge[]>) {
  const { error: errorToast } = usePixeToast()
  const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()
  const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

  const path = ref<string[]>([]) // TODO: deprecate?
  const pathEdges = ref<Edge[]>([])
  // const gatedPath = ref<string[]>([])
  // const gatedPathEdges = ref<string[]>([])
  //const pathIgnoringLocks = ref<string[]>([])
  const locked = ref<string[]>([])
  
  function isSoftGate(lock: PxLock) {
    return pxLockDefinitions.value.find((def) => def.id === lock.definition)!.soft_gate
  }

  const softGatedEdges = computed(() => {
    return edges.value.filter(edge => edge.data.locks.every((lock: PxLock) => isSoftGate(lock)))
  })

  const pathNodes = computed(() => {
    return path.value.map(nodeId => nodes.value.find(node => node.id === nodeId)!)
  })

  const pathNodesAndEdges = computed(() => {
    return Array.from(Array(pathNodes.value.length), (_, i) => ({ node: pathNodes.value[i], edge: pathEdges.value[i]}));
  })

  const gatedPath = computed(() => {
    let keys: PxKey[] = []
    const gatedNodes: Node[] = []
    const gatedEdges: Edge[] = []
    let softUnlock = false
    for(const step of pathNodesAndEdges.value) {
        if (softUnlock) {
            if (step.node) gatedNodes.push(step.node)
            if (step.edge) gatedEdges.push(step.edge)
        } else {
            if (step.node) keys = keys.concat(step.node.data.keys)
            if (isSoftUnlock(keys, step.edge?.data.locks)) {
                console.log(`soft unlock found on edge ${step.edge?.id}`)
                softUnlock = true
            }
        }
    }
    return { nodes: gatedNodes, edges: gatedEdges }
  })

  // TODO to use this reactively, pass definitions as props
  const lockDefinitionsMap = computed(() => {
    fetchPxLockDefinitions()
    return new Map(pxLockDefinitions.value.map(def => [def.id, def]));
  })

  function getKeysInNode(nodeId: string) {
    return nodes.value.find((node) => node.id === nodeId)!.data.keys
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

  // TODO: handle key definition ids instead of full key objects
  // assumes non-soft gate locks can be unlocked with available keys
  function isSoftUnlock(keys: PxKey[], locks: PxLock[]) {
    //console.log(`checking for soft unlock`)
    if (!locks || !locks.length) {
      return false
    }

    const softGates : PxLock[] = locks
      .filter((lock) => pxLockDefinitions.value.find((def) => def.id === lock.definition)!.soft_gate)

    return !canUnlock(keys, softGates, false)
  }

  function consumedLocks(keys: PxKey[], locks: PxLock[]) {

  }

  // current assumptions/limitations:
  // - keys are reusable. the same reusable key can be used to unlock multiple locks on the same edge
  // counts are ignored
  function canUnlock(keys: PxKey[], locks: PxLock[], unlockSoftGates: boolean = true) {
    if (!locks.length) {
      return true
    }

    // for set of locks, determine all sets of keys that can unlock them
    const requiredKeysPerLock: string[][] = locks
      .map((lock) => pxLockDefinitions.value.find((def) => def.id === lock.definition)!)
      .map((def) => def.soft_gate && unlockSoftGates ? [] : def.unlocked_by)
    //console.log(`requiredKeysPerLock: ${JSON.stringify(requiredKeysPerLock)}`)
    const unlockingKeySets: string[][] = cartesian(requiredKeysPerLock)
    // console.log(`unlockingKeySets: ${JSON.stringify(unlockingKeySets)}`)
    

    // edge is unlockable if any unlocking key set is a subset of the available keys
    const availableKeyDefs = keys.map((k) => k.definition)
    //console.log(`availableKeyDefs: ${JSON.stringify(availableKeyDefs)}`)
    const canUnlock = unlockingKeySets.some((set) => set.every((key) => availableKeyDefs.includes(key)))
    //console.log(`can unlock: ${canUnlock}`)
    return canUnlock
  }

  async function dijkstraInChart(sourceId: string, targetId: string, ignoreLocks: boolean = false) {
    // initialize
    if (!ignoreLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const q = [{ id: sourceId, prio: 0, keys: getKeysInNode(sourceId) }]
    const dist = new Map<string, number>()
    dist.set(sourceId, 0)
    const prev = new Map<string, string>()
    const prevEdges = new Map<string, Edge>()

    for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(node.id, Infinity)
        q.push({ id: node.id, prio: Infinity, keys: node.data.keys })
      }
    }

    // console.log(`queue: ${JSON.stringify(q)}`)

    // sort (descending so we can use pop)
    q.sort((n1, n2) => n2.prio - n1.prio)

    // iterate
    let found = false
    let inventory: PxKey[] = []
    let allLockedEdges: string[] = []
    while (q.length && !found) {
      const node = q.pop()
      if (!node) {
        break
      }
      // console.log(`node: ${JSON.stringify(node)}`)

      // let outs = getOutgoers(node.id, nodes.value, edges.value)
      let outEdges = getConnectedEdges(node.id, edges.value)
          .filter((edge) => edge.source === node.id)

      if (!ignoreLocks) {
        // update inventory
        if (node.keys && node.keys.length) {
          inventory = inventory.concat(node.keys)
        }
        // console.log(`inventory: ${JSON.stringify(inventory)}`)

        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = outEdges
          .reduce(
            (acc, edge) =>
              canUnlock(inventory, edge.data.locks)
                ? (acc[0].push(edge), acc)
                : (acc[1].push(edge), acc),
            [[], []] as [Edge[], Edge[]],
          )

        allLockedEdges = allLockedEdges.concat(lockedOutEdges.map((edge) => edge.id))

        // const unlockedOutNodeIds = unlockedOutEdges.map((edge) => edge.target)
        // outs = outs.filter((node) => unlockedOutNodeIds.includes(node.id))
        outEdges = unlockedOutEdges

        // clean up inventory
        // TODO: remove consumed locks
        inventory = inventory.filter(key => !pxKeyDefinitions.value.find(def => def.id === key.definition)!.fixed)
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

  async function dijkstraInChartMultiple(selected: string[], ignoreLocks: boolean = false) {
    let fullPath: string[] = []

    if (selected.length < 2) {
      return []
    }

    fullPath.push(selected[0]!)

    for (let i = 0; i < selected.length - 1; i++) {
      const nextSeq = await dijkstraInChart(selected[i]!, selected[i + 1]!, ignoreLocks)
      if (!nextSeq.length) {
        return []
      }
      fullPath = fullPath.concat(nextSeq.slice(1))
    }

    return fullPath
  }

  async function calculatePathFromSelection(selected: string[]) {
    console.log(`Starting path calculation...`)
    console.log(`Found ${nodes.value.length} nodes.`)
    console.log(`Input (length ${selected.length}): ${selected.toString()}`)
    let newPath: string[] = []
    //let newPathIgnoringLocks: string[] = []
    if (selected.length == 2 && selected[0] && selected[1]) {
      newPath = await dijkstraInChart(selected[0], selected[1])
      if (!newPath.length) {
        newPath = await dijkstraInChart(selected[1], selected[0])
      }

      /*
      if(!newPath.length) {
        newPathIgnoringLocks = await dijkstraInChart(selected[0], selected[1], true)
      }
      if (!newPathIgnoringLocks.length) {
        newPathIgnoringLocks = await dijkstraInChart(selected[1], selected[0], true)
      }*/
    } else {
      newPath = await dijkstraInChartMultiple(selected)

      /*
      if (!newPath.length) {
        newPathIgnoringLocks = await dijkstraInChartMultiple(selected, true)
      }
        */
    }

    if (!newPath.length) {
      errorToast('Could not calculate path between selected nodes.')
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
  }

  async function updatePathHighlight() {
    const pathNodeStyle = {
      // color: 'var(--ui-primary)',
      border: '3px solid var(--ui-primary)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-primary)',
    }

    // use warn color for path parts behind a soft gate
    const softGatedPathNodeStyle = {
      color: 'var(--ui-primary)',
      border: '3px solid var(--ui-warning)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-warning)',
    }

    // set style of nodes in calculated path
    for (const node of nodes.value) {
      node.style = path.value.includes(node.id) ? pathNodeStyle : undefined
    }
    for (const node of gatedPath.value.nodes) {
        node.style = softGatedPathNodeStyle
      }
  }

  async function updateEdgeStyling() {
    const lockedStyle = { stroke: 'var(--ui-error)' }
    const defaultPathStyle = { stroke: 'var(--ui-primary)' }
    const softGatedPathStyle = { stroke: 'var(--ui-warning)' } // TODO: check contrast

    //console.log(`pathNodesAndEdges: ${JSON.stringify(pathNodesAndEdges.value)}`)
    console.log(`gatedPath: ${JSON.stringify(gatedPath.value)}`)

    if (!path.value.length) {
      for (const edge of edges.value) {
        edge.style = locked.value.includes(edge.id) ? lockedStyle : undefined
      }
    } else {
      for (const edge of edges.value) {
        edge.style = pathEdges.value.includes(edge) ? defaultPathStyle : undefined
      }
      for (const edge of gatedPath.value.edges) {
        edge.style = softGatedPathStyle
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
