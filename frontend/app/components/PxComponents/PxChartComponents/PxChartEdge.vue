<script setup lang="ts">
import { type EdgeProps, SmoothStepEdge } from '@vue-flow/core'

const props = defineProps<EdgeProps<PxChartEdge>>()
const { fetchAll: fetchPxLocks, items: pxLocks } = usePxLocks(props.data.px_chart)

onMounted(() => {
  fetchPxLocks()
})

const locked = computed(() => {
  return pxLocks.value.filter((pxlock) => pxlock.edge === props.id).length > 0
})

async function updateLocks() {
  await fetchPxLocks()
}
</script>

<template>
  <SmoothStepEdge v-if="locked" v-bind="props" label="🔒" />
  <SmoothStepEdge v-else v-bind="props" />
</template>
