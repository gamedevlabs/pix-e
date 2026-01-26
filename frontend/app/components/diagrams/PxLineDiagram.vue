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

const data = computed(() => {
  const labels : string[] = []

  let relevantNodes = props.nodesInPath
    .map((name) => getNodeFromName(name))
    .filter((node) => node !== undefined)
  if (!relevantNodes.length)
    relevantNodes = pxNodes.value
  // console.log(`Nodes: [${relevantNodes.toString()}]`)
  
  relevantNodes.forEach((node) => {
    labels.push(node.name)
  })

  const datasets = []
  const colors = initColorIterator()

  selectedDefinitionIds.value.forEach((def) => {
    const values: number[] = []
    relevantNodes.forEach((node) => {
        const yValue = pxComponents.value
            .find((c) => c.definition === def && c.node === node.id)?.value
        if (typeof yValue === 'number') {
            values.push(yValue)
        } else {
            values.push(NaN)
        }
    })
    datasets.push({
        label: getNameFromDefinitionId(def),
        data: values,
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

const chartOptions = {
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
      }
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
}

const componentDefinitionNames = computed(() => {
    return pxComponentDefinitions.value.map((def) => def.name)
})

const selectedDefinitionIds: Ref<string[], string[]> = ref([])

async function handleDefinitionSelection(selection: string[]) {
  selectedDefinitionIds.value = pxComponentDefinitions.value
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
      <USelect
        v-if="componentDefinitionNames.length"
        placeholder="Select Component Definition"
        multiple
        :v-model="undefined" 
        :items="componentDefinitionNames"
        :ui="{ content: 'min-w-fit' }"
        @update:model-value="handleDefinitionSelection"
      />
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
      <p v-else>No data to display.<br/>ID of selected definitions: {{ selectedDefinitionIds }}<br/>Nodes: {{ pxNodes.toString() }}<br/>Data Labels: {{ data.labels.toString() }}<br/>Values: {{ data.datasets[0]?.data }}<br/>Path: {{ props.nodesInPath.toString() }}</p>
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

