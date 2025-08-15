<script setup lang="ts">
import PxGraphCanvas from '~/components/PxGraphComponents/PxGraphCanvas.vue'

definePageMeta({
  middleware: 'authentication',
})

const route = useRoute()
const chartId = route.params.id as string
</script>

<template>
  <div class="w-full h-full">
    <PxGraphCanvas :chart-id="chartId" />
  </div>
</template>

<style scoped></style>
