// types/px.ts

export type PXValueType = 'number' | 'string' | 'boolean' // extendable

export interface PXComponentDefinition {
  id: string
  name: string
  type: PXValueType
}

export interface PXNode {
  id: string
  name: string
  description: string
  values: Record<string, unknown> // key = component id, value = actual value
}

export interface PxNode {
  id: number
  name: string
  description: string
  owner: number | null
  created_at: string
  updated_at: string
}
