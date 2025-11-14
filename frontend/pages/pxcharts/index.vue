<script setup lang="ts">
import PxCardSection from '~/components/PxComponents/PxCardSection.vue'

definePageMeta({
  middleware: 'authentication',
})

const {
  items: pxCharts,
  fetchAll: fetchPxCharts,
  createItem: createPxChart,
  deleteItem: deletePxChart,
} = usePxCharts()

onMounted(() => {
  fetchPxCharts()
})

const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  await createPxChart({ ...newEntityDraft })
  newItem.value = null
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Px Charts</template>

      <PxCardSection use-add-button @add-clicked="addItem">
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
          <PxNamedEntityCard
            :named-entity="newItem"
            :is-being-edited="true"
            @edit="newItem = null"
            @update="createItem"
            @delete="newItem = null"
          />
        </div>
      </PxCardSection>
    </SimpleContentWrapper>
  </div>
</template>

<style scoped></style>
