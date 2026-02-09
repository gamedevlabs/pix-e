import type { Edge, Node } from '@vue-flow/core'
import { getOutgoers } from '@vue-flow/core'
import findIndex from 'lodash.findindex'

export function usePathsApi() {
  async function dijkstra_path(nodes: Node[], edges: Edge[], sourceId: string, targetId: string) {
    // initialize
    const q = [{ id: sourceId, prio: 0 }]
    const dist = new Map<string, number>()
    dist.set(sourceId, 0)
    const prev = new Map<string, string>()

    for (const node of nodes) {
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
      const outs = getOutgoers(node.id, nodes, edges)
      for (const out of outs) {
        const alt = dist.get(node.id) + 1
        if (alt < dist.get(out.id)) {
          prev.set(out.id, node.id)
          dist.set(out.id, alt)
          const idx = findIndex(q, ['id', out.id])
          q[idx].prio = alt
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
          current = prev.get(current)
        }
      }
    }

    return seq.reverse()
  }

  async function dijkstra_multiple(nodes: Node[], edges: Edge[], selected: Node[]) {
    const paths = new Map()

    for (const n1 of selected) {
      for (const n2 of selected) {
        const p = dijkstra_path(nodes, edges, n1.id, n2.id)
        paths.set({ n1: n1.id, n2: n2.id }, p)
      }
    }

    return
  }

  async function calculate_path(nodes: Node[], edges: Edge[], selected: string[]): Promise<string[]> {
    if (selected.length == 2 && selected[0] && selected[1]) {
      let path = dijkstra_path(nodes, edges, selected[0], selected[1])
      if (!(await path).length) {
        path = dijkstra_path(nodes, edges, selected[1], selected[0])
      }
      return path
    } else {
      return []
    }
  }

  return {
    calculate_path,
  }
}
