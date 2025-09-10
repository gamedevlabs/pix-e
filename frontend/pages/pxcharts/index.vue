<script setup lang="ts">
import { v4 } from 'uuid'

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
  const newUuid = v4()
  await createPxChart({ id: newUuid, ...newEntityDraft })
  newItem.value = null
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Px Charts</template>

      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="chart in pxCharts" :key="chart.id">
          <PxGraphCard
            :px-chart="chart"
            :visualization-style="'preview'"
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
