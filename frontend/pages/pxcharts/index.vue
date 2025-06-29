<script setup lang="ts">
const {
  fetchById: fetchPxDefinition,
  updateItem: updatePxDefinition,
  deleteItem: deletePxDefinition,
  loading: loadingPxDefinition,
  error: errorPxDefinition,
} = usePxCharts()

const fetchedDefinition = ref<PxChart | null>(null)

onMounted(() => {
  getDefinition()
})

async function getDefinition() {
  fetchedDefinition.value = await fetchPxDefinition(1)
}
</script>

<template>
  <div class="p-8">
    <div> {{fetchedDefinition}}</div>
    <div> Hello </div>
  </div>
</template>

<style scoped></style>
