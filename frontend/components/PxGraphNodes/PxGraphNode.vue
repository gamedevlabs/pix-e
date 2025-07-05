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

<style scoped></style>
