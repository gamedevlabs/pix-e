const pxValueTypes = ['none', 'number', 'string', 'boolean'] as const
type PxValueType = (typeof pxValueTypes)[number]

const pxContainerContentTypes = ['pxEmpty', 'pxNode'] as const
type PxContainerContentType = (typeof pxContainerContentTypes)[number]

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
  components: PxComponent[]
  charts: PxChart[]
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxChart extends NamedEntity {
  id: string
  name: string
  description: string
  associatedNode?: string | null
  containers: PxChartContainer[]
  edges: PxChartEdge[]
  owner?: number | null
  created_at: string
  updated_at: string
}

interface PxChartContainer {
  id: string
  name: string
  content: string | null
  type: PxContainerContentType
  layout: PxChartContainerLayout
  px_chart: string
  owner: number | null
  created_at: string
  updated_at: string
}

interface PxChartContainerLayout {
  position_x: number
  position_y: number
  width: number
  height: number
}

interface PxChartEdge {
  id: string
  px_chart: string
  source: string
  sourceHandle: string
  target: string
  targetHandle: string
  created_at: string
  updated_at: string
  owner: number | null
}
