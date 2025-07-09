const pxValueTypes = ['none', 'number', 'string', 'boolean'] as const
type PxValueType = (typeof pxValueTypes)[number]

interface PxComponentDefinition {
  id: number
  name: string
  type: PxValueType
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxComponent {
  id: number
  value: PxValueType
  created_at: string
  updated_at: string
  node: number
  definition: number
}

/*
interface PXNode {
  id: string
  name: string
  description: string
  values: Record<string, unknown> // key = component id, value = actual value
}
 */

interface PxNode extends NamedEntity {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxChart extends NamedEntity {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
  owner: number | null
  nodes: PxChartNode[]
  edges: PxChartEdge[]
}

interface PxChartNode {
  id: number
  name: string
  content: PxNode | null
  px_chart: number
  layout: PxChartNodeLayout
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxChartNodeLayout {
  position_x: number
  position_y: number
  width: number
  height: number
}

interface PxChartEdge {
  id: number
  px_chart: number
  source: number
  target: number
  created_at: string
  updated_at: string
  owner: number | null
}
