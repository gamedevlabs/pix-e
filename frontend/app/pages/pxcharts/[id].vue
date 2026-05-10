<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
})

const route = useRoute()
const chartId = route.params.id as string

const { currentProject } = useProjectHandler()
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

// px-1-3: "Open chart by clicking on its name"
onMounted(() => {
  toggleSubstep('px-1', 'px-1-3')
})

// track container count so we can distinguish first vs second add
const containerCount = ref(0)

async function handleContainerAdded() {
  containerCount.value++
  if (containerCount.value === 1) {
    // px-1-4: "Add a new container via the Add Icon"
    await toggleSubstep('px-1', 'px-1-4')
  } else if (containerCount.value === 2) {
    // px-1-5: "Add another container"
    await toggleSubstep('px-1', 'px-1-5')
  }
}

async function handleEdgeConnected() {
  // px-1-6: "Connect both containers"
  await toggleSubstep('px-1', 'px-1-6')
}

async function handleNodeAddedToContainer() {
  // px-2-4: "Open a chart and add a node to any container"
  await toggleSubstep('px-2', 'px-2-4')
}
</script>

<template>
  <div class="w-full h-full">
    <PxChartCanvas
      :chart-id="chartId"
      @container-added="handleContainerAdded"
      @edge-connected="handleEdgeConnected"
      @node-added-to-container="handleNodeAddedToContainer"
    />
  </div>
</template>

<style scoped></style>
