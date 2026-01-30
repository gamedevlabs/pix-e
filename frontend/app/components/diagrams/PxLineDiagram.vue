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
  id: {
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

const data = computed(() => {
  const labels : string[] = []
  const data: NodeData[] = []

  let relevantNodes = props.nodesInPath
    .map((name) => getNodeFromName(name))
    .filter((node) => node !== undefined)
  if (!relevantNodes.length)
    relevantNodes = pxNodes.value
  // console.log(`Nodes: [${relevantNodes.toString()}]`)

  // build and add NodeData object for each node
  let sumX: number = 0
  relevantNodes.forEach((node) => {
    // add node name
    const nodeData: NodeData = {
        name: node.name
    }
    labels.push(node.name)

    // add optional x value
    if (selectedDefinitionsX.value) {
        const xComp = pxComponents.value
            .find((c) => c.definition === selectedDefinitionsX.value && c.node === node.id)?.value
        if (typeof xComp === 'number') {
            sumX += xComp
        } else {
            sumX += 1
            // TODO: warning about invalid component type or missing component value
        }
        nodeData.x = sumX;
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
            xAxisKey: selectedDefinitionsX.value ? 'x' : undefined,
            yAxisKey: def,
        },
        stepped: selectedDefinitionsX.value ? 'after' : false,
        fill: true,
        borderColor: colors.next().value
    })
  })
  //console.log(`Labels: [${labels.toString()}]`)
  
  return {
        labels: labels,
        datasets: datasets
    }
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
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
      type: 'category',
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

const selectedDefinitionsX: Ref<string, string> = ref("")
const selectedDefinitionsY: Ref<string[], string[]> = ref([])

async function handleDefinitionSelectionX(selection: string) {
  const foundId = pxComponentDefinitions.value
    .find((def) => selection === def.name)?.id
  if (foundId) {
    selectedDefinitionsX.value = foundId
    chartOptions.value.scales.x.type = 'linear'
  } else {
    chartOptions.value.scales.x.type = 'category'
  }
}

async function handleDefinitionSelectionY(selection: string[]) {
  selectedDefinitionsY.value = pxComponentDefinitions.value
    .filter((def) => selection.includes(def.name))
    .map((def) => def.id)
}

function emitDelete() {
  emit('delete', props.id)
}

</script>

<template>
  
  <UCard>
    <template #header>
      <UFieldGroup>
        <UBadge color="neutral" variant="outline" size="lg" label="X" />
        <USelect
            v-if="componentDefinitionNames.length"
            placeholder="Select x-axis"
            :v-model="undefined" 
            :items="componentDefinitionNames"
            :ui="{ content: 'min-w-fit' }"
            @update:model-value="handleDefinitionSelectionX"
        />
      </UFieldGroup>
      <UFieldGroup>
        <UBadge color="neutral" variant="outline" size="lg" label="Y" />
        <USelect
            v-if="componentDefinitionNames.length"
            placeholder="Select y-axis"
            label="Y"
            multiple
            :v-model="undefined" 
            :items="componentDefinitionNames"
            :ui="{ content: 'min-w-fit' }"
            @update:model-value="handleDefinitionSelectionY"
        />
      </UFieldGroup>
      <UButton
            aria-label="Delete"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            @click="emitDelete"
      />  
    </template>
    <div class="chart-container">
      <Line v-if="data && data.datasets[0]?.data.some((v) => !!v)" :data="data" :options="chartOptions"/>
      <p v-else>No data to display.<br/>ID of selected definition: {{ selectedDefinitionsY }}<br/>Nodes: {{ pxNodes.toString() }}<br/>Data Labels: {{ data.labels?.toString() }}<br/>Values: {{ data.datasets[0]?.data }}<br/>Path: {{ props.nodesInPath.toString() }}</p>
    </div>
  </UCard>
</template>

<style scoped>
.chart-container {
  position: relative; 
  margin: auto;
  height: 30vh; 
  width: 100%;
}
</style>

