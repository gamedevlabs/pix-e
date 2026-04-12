<script setup lang="ts">
import { type EdgeProps, SmoothStepEdge } from '@vue-flow/core'

const props = defineProps<EdgeProps<PxChartEdge>>()

const locked = computed(() => {
  return props.data.locks && props.data.locks.length > 0
})
</script>

<template>
  <SmoothStepEdge
    v-bind="props"
    :label="locked ? '🔒' : undefined"
    :label-style="{ fontSize: 'x-large' }"
  />
</template>
