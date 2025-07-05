<script setup lang="ts">
import { Handle, type NodeProps } from '@vue-flow/core'
import { Position } from '@vue-flow/core'

const props = defineProps<NodeProps<PxChartNode>>()

console.log(props.data.name)
</script>

<template>
  <div>
    <Handle type="target" :position="Position.Top" />
    <div>{{ props.data.name }}</div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<style scoped>
/* these are necessary styles for vue flow */
@import '@vue-flow/core/dist/style.css';

/* this contains the default theme, these are optional styles */
@import '@vue-flow/core/dist/theme-default.css';
</style>
