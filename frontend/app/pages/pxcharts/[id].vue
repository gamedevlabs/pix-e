<script setup lang="ts">
import PxChartCanvas from '~/components/PxChartComponents/PxChartCanvas.vue'

definePageMeta({
  middleware: 'authentication',
})

const route = useRoute()
const chartId = route.params.id as string
</script>

<template>
  <div class="w-full h-full">
    <PxChartCanvas :chart-id="chartId" />
  </div>
</template>

<style scoped></style>
