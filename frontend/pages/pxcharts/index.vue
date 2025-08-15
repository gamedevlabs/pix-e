<script setup lang="ts">
import { v4 } from 'uuid'

definePageMeta({
  middleware: 'authentication',
})

const {
  items: pxCharts,
  fetchAll: fetchPxCharts,
  createItem: createPxChart,
  updateItem: updatePxChart,
  deleteItem: deletePxChart,
} = usePxCharts()

onMounted(() => {
  fetchPxCharts()
})

const editingId = ref<string | null>(null)

const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  const newUuid = v4()
  await createPxChart({ id: newUuid, ...newEntityDraft })
  newItem.value = null
}

async function handleUpdate(id: string, namedEntityDraft: Partial<NamedEntity>) {
  await updatePxChart(id, { ...namedEntityDraft })
  editingId.value = null
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
            :is-being-edited="editingId === chart.id"
            show-edit
            show-delete
            @edit="editingId = editingId === chart.id ? null : chart.id"
            @update="(namedEntityDraft) => handleUpdate(chart.id, namedEntityDraft)"
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
