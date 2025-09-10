<script setup lang="ts">
import { LazyPxGraphComponentsPxGraphContainerAddPxNodeForm } from '#components'

const props = defineProps<{
  pxChart: Partial<PxChart>
  isBeingEdited?: boolean
  showEdit?: boolean
  showDelete?: boolean
  visualizationStyle?: 'preview' | 'detailed'
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'edit' | 'delete' | 'removeNode'): void
  (event: 'addNode', nodeId: string): void
}>()

const {
  error: chartError,
  loading: chartLoading,
  fetchById: fetchChartById,
  updateItem: updateChart,
} = usePxCharts()

const draft = ref({ ...props.pxChart })

const fetchedChart = ref<PxChart>(null)

onMounted(() => {
  getChartInformation()
})

async function getChartInformation() {
  if (!props.pxChart.id) {
    console.error('No ID provided for PxGraphCard... Aborting')
    return
  }

  try {
    fetchedChart.value = await fetchChartById(props.pxChart.id!)
  } catch (err) {
    console.error(err)
  }
}

const overlay = useOverlay()
const modalAddPxNode = overlay.create(LazyPxGraphComponentsPxGraphContainerAddPxNodeForm)

watch(
  () => props.isBeingEdited,
  (newVal) => {
    if (newVal) {
      draft.value = { ...props.pxChart }
    }
  },
)

function emitEdit() {
  emit('edit')
}

function emitUpdate() {
  emit('update', draft.value)
}

function emitDelete() {
  emit('delete')
}

async function emitAddNode() {
  const nodeId = await modalAddPxNode.open().result

  if (!nodeId) return

  await updateChart(fetchedChart.value.id!, { associatedNode: nodeId })

  fetchedChart.value.associatedNode = nodeId

  emit('addNode', nodeId)
}

async function emitRemoveNode() {
  await updateChart(fetchedChart.value.id!, { associatedNode: null })

  fetchedChart.value.associatedNode = undefined

  emit('removeNode')
}
</script>

<template>
  <div v-if="chartError">
    <div v-if="chartError.response?.status === 403">You do not have access to this chart.</div>
    <div v-else-if="chartError.response?.status === 404">This chart does not exist.</div>
    <div v-else>Error loading Px Chart {{ pxChart.id }}</div>
  </div>
  <div v-else-if="chartLoading || !fetchedChart">Loading Px Chart {{ pxChart.id }}</div>
  <div v-else-if="fetchedChart">
    <PxGraphCardPreview v-if="visualizationStyle === 'preview'" :chart="fetchedChart" />
    <PxGraphCardDetailed v-else-if="visualizationStyle === 'detailed'" :chart="fetchedChart" />
  </div>
</template>

<style scoped></style>
