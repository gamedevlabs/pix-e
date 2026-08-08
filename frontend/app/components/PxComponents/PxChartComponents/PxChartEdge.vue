<script setup lang="ts">
import { type EdgeProps, SmoothStepEdge } from '@vue-flow/core'

const props = defineProps<EdgeProps<PxChartEdge>>()
</script>

<template>
  <SmoothStepEdge
    v-bind="props"
    :label-style="{ fontSize: 'x-large' }"
    :label-show-bg="false"
    :style="{ strokeWidth: '2px' }"
  />
</template>
