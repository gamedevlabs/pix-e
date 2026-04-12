import type { Edge, Node } from '@vue-flow/core'
import { getConnectedEdges, getOutgoers } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

export function usePxChartPathCalculation(nodes: Ref<Node[]>, edges: Ref<Edge[]>) {
  const { error: errorToast } = usePixeToast()
  const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()
  const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

  const path = ref<string[]>([])
  //const pathIgnoringLocks = ref<string[]>([])
  const locked = ref<string[]>([])

  function getKeys(id: string) {
    return nodes.value.find((node) => node.id === id)!.data.keys
  }

  function cartesian(sets: string[][]) {
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

  // current assumptions/limitations:
  // - keys are reusable. the same reusable key can be used to unlock multiple locks on the same edge
  // counts are ignored
  function canUnlock(keys: PxKey[], locks: PxLock[]) {
    if (!locks.length) {
      return true
    }

    // for set of locks, determine all sets of keys that can unlock them
    const requiredKeysPerLock: string[][] = locks
      .map((lock) => pxLockDefinitions.value.find((def) => def.id === lock.definition)!)
      .map((def) => def.unlocked_by)
    const unlockingKeySets: string[][] = cartesian(requiredKeysPerLock)

    // edge is unlockable if any unlocking key set is a subset of the available keys
    const availableKeyDefs = keys.map((k) => k.definition)
    return unlockingKeySets.some((set) => set.every((key) => availableKeyDefs.includes(key)))
  }

  async function dijkstraInChart(sourceId: string, targetId: string, ignoreLocks: boolean = false) {
    // initialize
    if (!ignoreLocks) {
      await fetchPxLockDefinitions()
      await fetchPxKeyDefinitions()
    }

    const q = [{ id: sourceId, prio: 0, keys: getKeys(sourceId) }]
    const dist = new Map<string, number>()
    dist.set(sourceId, 0)
    const prev = new Map<string, string>()

    for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(node.id, Infinity)
        q.push({ id: node.id, prio: Infinity, keys: node.data.keys })
      }
    }

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

      let outs = getOutgoers(node.id, nodes.value, edges.value)

      if (!ignoreLocks) {
        // update inventory
        if (node.keys && node.keys.length) {
          inventory = inventory.concat(node.keys)
        }

        // check for locked transitions
        const [unlockedOutEdges, lockedOutEdges] = getConnectedEdges(node.id, edges.value)
          .filter((edge) => edge.source === node.id)
          .reduce(
            (acc, edge) =>
              canUnlock(inventory, edge.data.locks)
                ? (acc[0].push(edge), acc)
                : (acc[1].push(edge), acc),
            [[], []] as [Edge[], Edge[]],
          )

        allLockedEdges = allLockedEdges.concat(lockedOutEdges.map((edge) => edge.id))

        const unlockedOutNodeIds = unlockedOutEdges.map((edge) => edge.target)
        outs = outs.filter((node) => unlockedOutNodeIds.includes(node.id))

        // clean up inventory
        inventory = inventory.filter(key => !pxKeyDefinitions.value.find(def => def.id === key.definition)!.fixed)
      }

      for (const out of outs) {
        const alt = dist.get(node.id)! + 1
        if (alt < dist.get(out.id)!) {
          prev.set(out.id, node.id)
          dist.set(out.id, alt)
          const idx = findIndex(q, ['id', out.id])
          q[idx]!.prio = alt
          q.sort((n1, n2) => n2.prio - n1.prio)
        }
        if (out.id == targetId) {
          found = true
          break
        }
      }
    }

    const seq = []
    if (found) {
      // construct sequence
      let current = targetId
      if (prev.has(current) || current == sourceId) {
        while (current) {
          seq.push(current)
          current = prev.get(current)!
        }
      }
    }

    locked.value = locked.value.concat(allLockedEdges)
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
    locked.value = []
  }

  async function updatePathHighlight() {
    const pathStyle = {
      color: 'var(--ui-primary)',
      border: '3px solid var(--ui-primary)',
      borderRadius: '10px',
      boxShadow: '0 0 10px var(--ui-primary)',
    }

    // set style of nodes in calculated path
    for (const node of nodes.value) {
      node.style = path.value.includes(node.id) ? pathStyle : undefined
    }
  }

  async function updateEdgeStyling() {
    const lockedStyle = { stroke: 'var(--ui-error)' }

    if (!path.value.length) {
      for (const edge of edges.value) {
        edge.style = locked.value.includes(edge.id) ? lockedStyle : undefined
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
