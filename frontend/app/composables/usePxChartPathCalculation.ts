import type { Edge, Node } from '@vue-flow/core'
import { getOutgoers } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

export function usePxChartPath(nodes: Ref<Node[]>, edges: Ref<Edge[]>) {
  const { error: errorToast } = usePixeToast()

  const path = ref<string[]>([])

  async function dijkstraInChart(sourceId: string, targetId: string) {
    // initialize
    const q = [{ id: sourceId, prio: 0 }]
    const dist = new Map<string, number>()
    dist.set(sourceId, 0)
    const prev = new Map<string, string>()

    for (const node of nodes.value) {
      if (node.id != sourceId) {
        dist.set(node.id, Infinity)
        q.push({ id: node.id, prio: Infinity })
      }
    }

    // sort (descending so we can use pop)
    q.sort((n1, n2) => n2.prio - n1.prio)

    // iterate
    let found = false
    while (q.length && !found) {
      const node = q.pop()
      if (!node) {
        break
      }
      const outs = getOutgoers(node.id, nodes.value, edges.value)
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

    return seq.reverse()
  }

  async function dijkstraInChartMultiple(selected: string[]) {
    let fullPath: string[] = []

    if (selected.length < 2) {
      return []
    }

    fullPath.push(selected[0]!)

    for (let i = 0; i < selected.length - 1; i++) {
      const nextSeq = await dijkstraInChart(selected[i]!, selected[i + 1]!)
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
    if (selected.length == 2 && selected[0] && selected[1]) {
      newPath = await dijkstraInChart(selected[0], selected[1])
      if (!newPath.length) {
        newPath = await dijkstraInChart(selected[1], selected[0])
      }
    } else {
      newPath = await dijkstraInChartMultiple(selected)
    }

    if (!newPath.length) {
      errorToast('Failed to calculate path between selected nodes.')
    }
    path.value = newPath
    console.log(
      `Finished path calculation!\nResult (length ${path.value.length}): ${path.value.toString()}`,
    )
  }

  async function resetPathValue() {
    // reset path itself
    path.value = []
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

  return {
    path,
    calculatePathFromSelection,
    resetPathValue,
    updatePathHighlight,
  }
}
