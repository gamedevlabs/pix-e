<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
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
