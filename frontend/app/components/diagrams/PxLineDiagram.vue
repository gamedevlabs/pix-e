<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale } from 'chart.js'

const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()
const { items: pxComponentDefinitions, fetchAll: fetchPxComponentDefinitions } = usePxComponentDefinitions()

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale)

onMounted(() => {
  fetchPxNodes()
  fetchPxComponents()
  fetchPxComponentDefinitions()
})

const props = defineProps({
  nodesInPath: {
    type: Array<string>,
    default: () => [],
  },
  diagramId: {
    type: String,
    default: () => ''
  }
})

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'delete', diagramId: string): void
}>()

function getNameFromDefinitionId(id: string) {
    return pxComponentDefinitions.value.find((def) => def.id === id)?.name
}

function getNodeFromName(name: string) {
    return pxNodes.value.find((node) => node.name === name)
}

function initColorIterator() {
  let idx = 0;

  const colors = [
    '#06b6d4',
    '#164e63',
    '#93c5fd',
    '#1e3a8a',
    '#d1d5db',
    '#1f2937'
  ]

  const colorIterator = {
    next() {
      const result = { value: colors[idx % colors.length], done: false };
      idx++;
      return result;
    },
  };
  return colorIterator;
}

interface NodeData {
    name: string;
    [key: string]: string | number | boolean | undefined;
}

const relevantNodes = computed(() => {
    let relevantNodes = props.nodesInPath
        .map((name) => getNodeFromName(name))
        .filter((node) => node !== undefined)

    if (!relevantNodes.length)
        relevantNodes = pxNodes.value
    
    return relevantNodes
})

const nodeLabels = computed(() => {
    const labels : string[] = []

    relevantNodes.value.forEach((node) => {
        labels.push(node.name)
    })

    return labels
})

const data = computed(() => {
  const data: NodeData[] = []

  // build and add NodeData object for each node
  let sumXValue: number = 0
  const sumXID: string = 'sum-'.concat(selectedDefinitionsX.value)

  relevantNodes.value.forEach((node) => {
    // add node name
    const nodeData: NodeData = {
        name: node.name
    }

    // add optional x value
    if (selectedDefinitionsX.value) {
        const xComp = pxComponents.value
            .find((c) => c.definition === selectedDefinitionsX.value && c.node === node.id)?.value
        sumXValue += (typeof xComp === 'number') ? xComp : 1;
        nodeData[sumXID] = sumXValue;
    }

    // add values for Y-axis components
    pxComponents.value
        .filter((c) => selectedDefinitionsY.value.includes(c.definition) && c.node === node.id)
        .forEach((c) => { nodeData[c.definition] = c.value })

    data.push(nodeData)
  })

  const datasets = []
  const colors = initColorIterator()

  selectedDefinitionsY.value.forEach((def) => {
    datasets.push({
        label: getNameFromDefinitionId(def),
        data: data,
        parsing: {
            xAxisKey: selectedDefinitionsX.value ? sumXID : 'name',
            yAxisKey: def,
        },
        stepped: selectedDefinitionsX.value ? 'after' : false,
        fill: true,
        borderColor: colors.next().value
    })
  })
  //console.log(`Labels: [${labels.toString()}]`)
  //alert(JSON.stringify(datasets))
  
  return {
        labels: nodeLabels.value,
        datasets: datasets
    }
})

const xAxisType = ref('category')

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    x: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
      type: xAxisType.value
    },
    y: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      }
    },
  },
}))

const chartOptions2 = ref({
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    x: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
      type: 'category'
    },
    y: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      }
    },
  },
})

const componentDefinitionNames = computed(() => {
    return pxComponentDefinitions.value.map((def) => def.name)
})

const selectedDefinitionsX: Ref<string, string> = ref('')
const selectedDefinitionsY: Ref<string[], string[]> = ref([])

async function handleDefinitionSelectionX(selection: string) {
  const foundId = pxComponentDefinitions.value
    .find((def) => selection === def.name)?.id
  if (foundId) {
    selectedDefinitionsX.value = foundId
    xAxisType.value = 'linear'
    chartOptions2.value.scales.x.type = 'linear'
    // alert(`Changed x axis type to linear: ${JSON.stringify(chartOptions2.value)}`)
  } else {
    selectedDefinitionsX.value = ''
    xAxisType.value = 'category'
    chartOptions2.value.scales.x.type = 'category'
  }
  //alert(`New X axis ID: ${selectedDefinitionsX.value}`)
}

async function handleDefinitionSelectionY(selection: string[]) {
  selectedDefinitionsY.value = pxComponentDefinitions.value
    .filter((def) => selection.includes(def.name))
    .map((def) => def.id)
}

function emitDelete() {
  emit('delete', props.diagramId)
}

</script>

<template>
  
  <UCard>
    <template #header>
        <div class="grid grid-cols-2 gap-6">
        <UFieldGroup>
            <UBadge color="neutral" variant="outline" size="lg" label="X" />
            <USelect
                v-if="componentDefinitionNames.length"
                placeholder="Select Component"
                :v-model="undefined" 
                :items="componentDefinitionNames"
                :ui="{ content: 'min-w-fit' }"
                :content="{
                    align: 'start',
                    side: 'right',
                    sideOffset: 8
                }"
                @update:model-value="handleDefinitionSelectionX"
            /> 
        </UFieldGroup>
        <UFieldGroup>
            <UBadge color="neutral" variant="outline" size="lg" label="Y" />
            <USelect
                v-if="componentDefinitionNames.length"
                placeholder="Select Components"
                label="Y"
                multiple
                :v-model="undefined" 
                :items="componentDefinitionNames"
                :ui="{ content: 'min-w-fit' }"
                :content="{
                    align: 'start',
                    side: 'right',
                    sideOffset: 8
                }"
                @update:model-value="handleDefinitionSelectionY"
            />
        </UFieldGroup>
        </div>
    </template>
    <div class="chart-container">
      <Line 
        v-if="data && data.datasets[0]?.data.some((v) => !!v)" 
        :data="data" 
        :options="chartOptions2"
      />
      <p v-else>No data to display.</p>
    </div>
    <template #footer>
      <UButton
            aria-label="Delete"
            color="error"
            variant="soft"
            label="Remove Diagram"
            @click="emitDelete"
      />  
    </template>
  </UCard>
</template>

<style scoped>
.chart-container {
  position: relative; 
  margin: auto; 
  width: 100%;
}
</style>

