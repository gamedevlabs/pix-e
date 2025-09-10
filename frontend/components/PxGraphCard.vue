<script setup lang="ts">

const props = defineProps<{
  pxChart: Partial<PxChart>
  visualizationStyle?: 'preview' | 'detailed'
}>()

const { error: chartError, loading: chartLoading, fetchById: fetchChartById, deleteItem: deleteChart, updateItem: updatePxChart } = usePxCharts()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<NamedEntity>): void
  (event: 'edit' | 'delete', graphId: string): void
}>()

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

function emitEdit(graphId: string) {
  emit('edit', graphId)
}

async function handleDelete(graphId: string) {
  emit('delete', graphId)
}

async function handleUpdate(updatedPxChart: Partial<PxChart>) {
  await updatePxChart(updatedPxChart.id!, { ...updatedPxChart })
  await getChartInformation()
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
    <PxGraphCardPreview v-if="visualizationStyle === 'preview'" :chart="fetchedChart" @edit="emitEdit" @update="handleUpdate" @delete="handleDelete" />
    <PxGraphCardDetailed v-else-if="visualizationStyle === 'detailed'" :chart="fetchedChart" @edit="emitEdit" @update="handleUpdate" @delete="handleDelete" />
  </div>
</template>

<style scoped></style>
