<script setup lang="ts">
import { ref, watchEffect } from 'vue'

const props = defineProps({
  heatmapData: {
    type: Object,
    required: true,
  },
})

const aspects = ref([])
const years = ref([])
const maxValue = ref(1)

watchEffect(() => {
  if (!props.heatmapData || Object.keys(props.heatmapData).length === 0) return

  aspects.value = Object.keys(props.heatmapData)

  const firstAspect = aspects.value[0]
  years.value = Object.keys(props.heatmapData[firstAspect] || {}).sort()

  const allValues = Object.values(props.heatmapData).flatMap((row) => Object.values(row))
  maxValue.value = Math.max(...allValues, 1)
})

const getIntensity = (value, max) => {
  const ratio = value / max
  if (ratio === 0) return 'bg-gray-100'
  if (ratio < 0.25) return 'bg-blue-100'
  if (ratio < 0.5) return 'bg-blue-300'
  if (ratio < 0.75) return 'bg-blue-500'
  return 'bg-blue-700 text-white'
}
</script>

<template>
  <div v-if="aspects.length && years.length" class="overflow-x-auto">
    <table class="table-auto border border-gray-300 text-sm">
      <thead class="bg-gray-200">
        <tr>
          <th class="px-2 py-1 text-left">Aspect</th>
          <th v-for="year in years" :key="year" class="px-2 py-1 text-center">
            {{ year }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="aspect in aspects" :key="aspect">
          <td class="border px-2 py-1 font-medium">{{ aspect }}</td>
          <td v-for="year in years" :key="year" class="border px-2 py-1 text-center">
            <span
              :class="getIntensity(props.heatmapData[aspect]?.[year] || 0, maxValue)"
              class="block w-full rounded py-0.5"
            >
              {{ props.heatmapData[aspect]?.[year] || 0 }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-else class="text-gray-500 text-sm">Loading heatmap data...</div>
</template>
