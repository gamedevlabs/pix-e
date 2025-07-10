const pxValueTypes = ['none', 'number', 'string', 'boolean'] as const
type PxValueType = (typeof pxValueTypes)[number]

interface PxComponentDefinition {
  id: string
  name: string
  type: PxValueType
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxComponent {
  id: string
  value: PxValueType
  created_at: string
  updated_at: string
  node: string
  definition: string
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
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxChart extends NamedEntity {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
  owner: number | null
  nodes: PxChartNode[]
  edges: PxChartEdge[]
}

interface PxChartNode {
  id: string
  name: string
  content: PxNode | null
  px_chart: string
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
  id: string
  px_chart: string
  source: string
  target: string
  created_at: string
  updated_at: string
  owner: number | null
}
