<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
} from 'chart.js'

import {
  lineCategoryOptions,
  lineLinearOptions,
  getDefaultLineDatasetOptions,
} from './DiagramOptions'
import { type NodeData, initColorIterator } from './DiagramUtils'

ChartJS.register(
    Title,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    LineElement,
    PointElement,
)

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

const selectedXLabel = defineModel<string>('selectedXLabel', {
  default: 'Nodes',
})

const selectedDefinitionsX = defineModel<string>('selectedDefinitionsX', {
  default: '',
})

const selectedDefinitionsY = defineModel<string[]>('selectedDefinitionsY', {
  default: () => [],
})

const chartKey = computed(() =>
    JSON.stringify({
      data: props.nodeData,
      labels: props.nodeLabels,
      x: selectedDefinitionsX.value,
      y: selectedDefinitionsY.value,
    }),
)

async function handleDefinitionSelectionX(selection: string) {
  selectedXLabel.value = selection

  const foundId = props.pxComponentDefinitions.find((def) => selection === def.name)?.id

  selectedDefinitionsX.value = foundId ?? ''
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
  <UCard
    class="min-h-55 transition-all hover:ring hover:ring-primary hover:shadow-lg hover:bg-default"
    variant="subtle"
  >
    <template #header>
      <div class="flex items-center gap-3 w-full">
        <UTooltip text="Remove Diagram">
          <UButton
            class="shrink-0"
            icon="lucide-trash"
            aria-label="Delete"
            color="error"
            variant="soft"
            square
            @click="emitDelete"
          />
        </UTooltip>

        <div class="grid grid-cols-2 gap-6 flex-1 min-w-0">
          <UFieldGroup class="min-w-0">
            <UBadge color="neutral" variant="outline" size="lg" label="f(X)" />
            <USelect
              v-if="numericalComponentDefinitionNames.length"
              class="w-full"
              placeholder="Select Components"
              multiple
              :items="numericalComponentDefinitionNames"
              :ui="{ content: 'min-w-fit' }"
              :content="{ align: 'start', side: 'right', sideOffset: 8 }"
              @update:model-value="handleDefinitionSelectionY"
            />
          </UFieldGroup>

          <UFieldGroup class="min-w-0">
            <UBadge color="neutral" variant="outline" size="lg" label="X" />
            <USelect
              v-if="numericalComponentDefinitionNames.length"
              v-model="selectedXLabel"
              class="w-full"
              placeholder="Select Component"
              :items="['Nodes', ...numericalComponentDefinitionNames]"
              :ui="{ content: 'min-w-fit' }"
              :content="{ align: 'start', side: 'right', sideOffset: 8 }"
              @update:model-value="handleDefinitionSelectionX"
            />
          </UFieldGroup>
        </div>
      </div>
    </template>

    <div class="relative mx-auto w-full min-h-l">
      <Line
        v-if="data && data.datasets[0]?.data.some((v: NodeData) => !!v) && selectedDefinitionsX"
        :key="`linear-${chartKey}`"
        :data="data"
        :options="lineLinearOptions"
      />
      <Line
        v-else-if="data && data.datasets[0]?.data.some((v: NodeData) => !!v)"
        :key="`category-${chartKey}`"
        :data="data"
        :options="lineCategoryOptions"
      />
      <p v-else>No data to display.</p>
    </div>
  </UCard>
</template>

<style scoped></style>
