// types/px.d.ts
export {}

declare global {
  type PXValueType = 'number' | 'string' | 'boolean' // extendable

  interface PXComponentDefinition {
    id: string
    name: string
    type: PXValueType
  }

  interface PXNode {
    id: string
    name: string
    description: string
    values: Record<string, unknown> // key = component id, value = actual value
  }

  interface PxNode {
    id: number
    name: string
    description: string
    owner: number | null
    created_at: string
    updated_at: string
  }
}
