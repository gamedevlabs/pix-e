<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Charts',
    icon: 'i-lucide-chart-network',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 1,
    showInNav: true,
  },
})
// ============================================================================

const {
  items: pxCharts,
  fetchAll: fetchPxCharts,
  createItem: createPxChart,
  deleteItem: deletePxChart,
} = usePxCharts()

const { currentProject } = useProjectHandler()
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

onMounted(() => {
  fetchPxCharts()
  // px-1-1: "Open Charts page"
  toggleSubstep('px-1', 'px-1-1')
})

const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  await createPxChart({ ...newEntityDraft })
  // px-1-2: "Create a new chart"
  await toggleSubstep('px-1', 'px-1-2')
  newItem.value = null
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Charts</template>

      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="chart in pxCharts" :key="chart.id">
          <PxChartCard
            :px-chart="chart"
            :visualization-style="'detailed'"
            show-edit
            show-delete
            @delete="deletePxChart(chart.id)"
          />
        </div>
        <div v-if="newItem">
          <NamedEntityCard
            :named-entity="newItem"
            :is-being-edited="true"
            @edit="newItem = null"
            @update="createItem"
            @delete="newItem = null"
          />
        </div>
      </SimpleCardSection>
    </SimpleContentWrapper>
  </div>
</template>

<style scoped></style>
