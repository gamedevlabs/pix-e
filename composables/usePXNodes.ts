// composables/usePXGraph.ts
import { ref } from 'vue'
import { v4 as uuid } from 'uuid'
import type { PXComponentDefinition, PXNode, PXValueType } from '@/types/px'

export function usePXGraph() {
  const componentDefs = ref<PXComponentDefinition[]>([])
  const nodes = ref<PXNode[]>([])

  // -----------------
  // Creation
  // -----------------
  function createComponentDef(name: string, type: PXValueType): PXComponentDefinition {
    const comp = { id: uuid(), name, type }
    componentDefs.value.push(comp)
    return comp
  }

  function createNode(name: string, description: string): PXNode {
    const node = { id: uuid(), name, description, values: {} }
    nodes.value.push(node)
    return node
  }

  // -----------------
  // Attachment
  // -----------------
  function attachComponentToNode(nodeId: string, compId: string, value: unknown) {
    const node = nodes.value.find((n) => n.id === nodeId)
    const def = componentDefs.value.find((d) => d.id === compId)
    if (!node || !def) return

    // You could add validation here if needed (e.g., check typeof)
    node.values[compId] = value
  }

  function removeComponentFromNode(nodeId: string, compId: string) {
    const node = nodes.value.find((n) => n.id === nodeId)
    if (node && node.values[compId] !== undefined) {
      // Save way to delete compId from array
      const { [compId]: _, ...rest } = node.values
      node.values = rest
    }
  }

  // -----------------
  // Accessors
  // -----------------
  function getComponentValue(node: PXNode, compId: string): unknown {
    return node.values[compId]
  }

  function getAttachedComponents(node: PXNode): PXComponentDefinition[] {
    return componentDefs.value.filter((c) =>
      Object.prototype.hasOwnProperty.call(node.values, c.id),
    )
  }

  return {
    componentDefs,
    nodes,
    createComponentDef,
    createNode,
    attachComponentToNode,
    removeComponentFromNode,
    getComponentValue,
    getAttachedComponents,
  }
}
