<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale,
  LinearScale,
} from 'chart.js'

import {
  lineCategoryOptions,
  lineLinearOptions,
  getDefaultLineDatasetOptions,
} from './DiagramOptions'
import { type NodeData, initColorIterator } from './DiagramUtils'

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale)

const props = defineProps({
  nodeData: {
    type: Array<NodeData>,
    default: () => [],
  },
  nodeLabels: {
    type: Array<string>,
    default: () => [],
  },
  pxComponentDefinitions: {
    type: Array<PxComponentDefinition>,
        default: () => [],
  },
  diagramId: {
    type: String,
    default: () => '',
  },
})

const emit = defineEmits<{
  (event: 'delete', diagramId: string): void
}>()

function getNameFromDefinitionId(id: string) {
  return props.pxComponentDefinitions.find((def) => def.id === id)?.name
}

// specify which of the pre-computed data to visualize
const data = computed(() => {
  const datasets = []
  const colors = initColorIterator()
  const sumXID: string = 'sum-'.concat(selectedDefinitionsX.value)

  selectedDefinitionsY.value.forEach((def) => {
    const color = colors.next().value
    datasets.push({
      label: getNameFromDefinitionId(def),
      data: props.nodeData,
      parsing: {
        xAxisKey: selectedDefinitionsX.value ? sumXID : 'name',
        yAxisKey: def,
      },
      stepped: selectedDefinitionsX.value ? 'after' : false,
      ...getDefaultLineDatasetOptions(color),
    })
  })

  return {
    labels: props.nodeLabels,
    datasets: datasets,
  }
})

const numericalComponentDefinitionNames = computed(() => {
  return props.pxComponentDefinitions.filter((def) => def.type === 'number').map((def) => def.name)
})

const selectedDefinitionsX: Ref<string, string> = ref('')
const selectedDefinitionsY: Ref<string[], string[]> = ref([])

async function handleDefinitionSelectionX(selection: string) {
  // check whether selection is actual component or dummy option for equal spacing
  const foundId = props.pxComponentDefinitions.find((def) => selection === def.name)?.id
  if (foundId) {
    selectedDefinitionsX.value = foundId
  } else {
    selectedDefinitionsX.value = ''
  }
}

async function handleDefinitionSelectionY(selection: string[]) {
  selectedDefinitionsY.value = props.pxComponentDefinitions
    .filter((def) => selection.includes(def.name))
    .map((def) => def.id)
}

function emitDelete() {
  emit('delete', props.diagramId)
}
</script>

<template>
  <UCard class="min-h-55">
    <template #header>
      <div class="grid grid-cols-2 gap-6">
        <UFieldGroup>
          <UBadge color="neutral" variant="outline" size="lg" label="X" />
          <USelect
            v-if="numericalComponentDefinitionNames.length"
            placeholder="Select Component"
            :v-model="undefined"
            :items="['None'].concat(numericalComponentDefinitionNames)"
            :ui="{ content: 'min-w-fit' }"
            :content="{
              align: 'start',
              side: 'right',
              sideOffset: 8,
            }"
            @update:model-value="handleDefinitionSelectionX"
          />
        </UFieldGroup>
        <UFieldGroup>
          <UBadge color="neutral" variant="outline" size="lg" label="Y" />
          <USelect
            v-if="numericalComponentDefinitionNames.length"
            placeholder="Select Components"
            label="Y"
            multiple
            :v-model="undefined"
            :items="numericalComponentDefinitionNames"
            :ui="{ content: 'min-w-fit' }"
            :content="{
              align: 'start',
              side: 'right',
              sideOffset: 8,
            }"
            @update:model-value="handleDefinitionSelectionY"
          />
        </UFieldGroup>
      </div>
    </template>
    <div class="chart-container">
      <Line
        v-if="data && data.datasets[0]?.data.some((v: NodeData) => !!v) && selectedDefinitionsX"
        :data="data"
        :options="lineLinearOptions"
      />
      <Line
        v-else-if="data && data.datasets[0]?.data.some((v: NodeData) => !!v)"
        :data="data"
        :options="lineCategoryOptions"
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
