<script setup lang="ts">
import { v4 } from 'uuid'
import { computed } from 'vue'

import type { NodeData } from './DiagramUtils'

definePageMeta({
  middleware: 'authentication',
})

const props = defineProps({
  nodesInPath: {
    type: Array<string | null>,
    default: () => [],
  },
  pxNodes: {
    type: Array<PxNode>,
    default: () => [],
  },
  pxComponents: {
    type: Array<PxComponent>,
    default: () => [],
  },
  pxComponentDefinitions: {
    type: Array<PxComponentDefinition>,
    default: () => [],
  },
})

const diagrams = ref(new Array<string>())
type DiagramState = {
  selectedXLabel: string
  selectedDefinitionsX: string
  selectedDefinitionsY: string[]
}

const diagramState = ref<Record<string, DiagramState>>({})

const carousel = useTemplateRef('carousel')

async function addDiagramAndShow() {
  addItem()

  await nextTick()

  carousel.value?.emblaApi?.scrollTo(diagrams.value.length - 1)
}

function addItem() {
  const newUuid = v4()
  diagrams.value.push(newUuid)

  diagramState.value[newUuid] = {
    selectedXLabel: 'Nodes',
    selectedDefinitionsX: '',
    selectedDefinitionsY: [],
  }
}

async function deleteDiagram(deleteId: string) {
  diagrams.value = diagrams.value.filter((id) => id != deleteId)

  const { [deleteId]: _, ...remaining } = diagramState.value
  diagramState.value = remaining
}

const dummyNode: PxNode = {
  id: '',
  name: 'null',
  description: '',
  components: [],
  charts: [],
  created_at: '',
  updated_at: '',
  owner: null,
}

function getNodeFromName(name: string | null) {
  if (name) {
    return props.pxNodes.find((node) => node.name === name)
  } else {
    return dummyNode
  }
}

const relevantNodes = computed(() => {
  let relevantNodes = props.nodesInPath
    .map((name) => getNodeFromName(name))
    .filter((node) => node !== undefined)

  if (!relevantNodes.length) relevantNodes = props.pxNodes

  return relevantNodes
})

// put node data in proper format for chartjs once,
// so it can be reused for different diagram types and axis configurations
const allData = computed(() => {
  const allNodeData: NodeData[] = []

  // aggregator for x-axis components
  const sumsXComponents = Object.fromEntries(
    props.pxComponentDefinitions
      .filter((c) => c.type === 'number')
      .map((c) => ['sum-'.concat(c.id), 0]),
  )

  relevantNodes.value.forEach((node) => {
    // add node name
    const nodeData: NodeData = {
      name: node.name,
    }

    // add values for components, including sums for numerical x-axis components
    props.pxComponents
      .filter((c) => c.node === node.id)
      .forEach((c) => {
        nodeData[c.definition] = c.value

        if (typeof c.value === 'number') {
          const sumXID: string = 'sum-'.concat(c.definition)

          sumsXComponents[sumXID]! += typeof c.value === 'number' ? c.value : 1
          nodeData[sumXID] = sumsXComponents[sumXID]
        }
      })

    allNodeData.push(nodeData)
  })

  return allNodeData
})

const nodeLabels = computed(() => {
  const labels: string[] = []

  relevantNodes.value.forEach((node) => {
    labels.push(node.name)
  })

  return labels
})
</script>

<template>
  <div>
    <UCarousel
      ref="carousel"
      v-slot="{ item }"
      dots
      :items="diagrams"
      class="w-full max-w-xl mx-auto"
      :ui="{
        viewport: 'overflow-hidden',
        container: 'items-end',
        item: 'basis-full shrink-0 grow-0',
      }"
    >
      <div :key="item" class="w-xl max-w-full mx-auto p-2">
        <PxLineDiagram
          :key="item"
          v-model:selected-x-label="diagramState[item].selectedXLabel"
          v-model:selected-definitions-x="diagramState[item].selectedDefinitionsX"
          v-model:selected-definitions-y="diagramState[item].selectedDefinitionsY"
          :node-data="allData"
          :node-labels="nodeLabels"
          :px-component-definitions="pxComponentDefinitions"
          :diagram-id="item"
          show-edit
          show-delete
          @delete="deleteDiagram"
        />
      </div>
    </UCarousel>
    <UTooltip text="Add Diagram">
      <UButton icon="lucide-plus" class="m-2" @click="addDiagramAndShow" />
    </UTooltip>
  </div>
</template>

<style scoped></style>
