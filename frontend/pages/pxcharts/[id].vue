<script setup lang = "ts">
const route = useRoute()
const id = route.params.id as unknown as number

const {
  fetchById: fetchPxGraph,
} = usePxCharts()

const chart = ref<PxChart | null>(null)

onMounted(() => {
  getDefinition()
})

async function getDefinition() {
  chart.value = await fetchPxGraph(id)
}
</script>

<template>
  <div class="p-4" v-if="chart">
    <h1 class="text-2xl font-bold">{{ chart.name }}</h1>
    <p class="text-gray-600 mb-4">{{ chart.description }}</p>

    <div class="mb-6">
      <h2 class="text-xl font-semibold">Nodes</h2>
      <ul class="list-disc ml-6">
        <li v-for="node in chart.nodes" :key="node.id">
          <strong>{{ node.name }}</strong>: {{ node.content }}
        </li>
      </ul>
    </div>

    <div>
      <h2 class="text-xl font-semibold">Edges</h2>
      <ul class="list-disc ml-6">
        <li v-for="edge in chart.edges" :key="edge.id">
          {{ edge.source }} → {{ edge.destination }}
        </li>
      </ul>
    </div>
  </div>
</template>
