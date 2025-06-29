<script setup lang="ts">
const { items: pxCharts, fetchAll: fetchPxCharts } = usePxCharts()

onMounted(() => {
  fetchPxCharts()
})
</script>

<template>
  <div class="p-8">
    <div v-for="chart in pxCharts" :key="chart.id">{{ chart }}</div>
  </div>
</template>

<style scoped></style>
