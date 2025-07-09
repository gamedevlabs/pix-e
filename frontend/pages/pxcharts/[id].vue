<script setup lang="ts">
import PxGraphCanvas from '~/components/PxGraphComponents/PxGraphCanvas.vue'

const route = useRoute()
const chartId = route.params.id as string
</script>

<template>
  <PxGraphCanvas :chart-id="chartId" />
</template>

<style scoped></style>
