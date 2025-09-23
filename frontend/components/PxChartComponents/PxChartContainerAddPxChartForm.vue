<script setup lang="ts">
const { items: pxCharts, fetchAll: fetchPxCharts } = usePxCharts()

onMounted(() => {
  fetchPxCharts()
})

const emit = defineEmits<{ close: [number] }>()

const selectedChartId = ref(-1)

async function onSubmit() {
  emit('close', selectedChartId.value)
}
</script>

<template>
  <UModal :title="'Add new Component'">
    <template #body>
      <UForm :state="selectedChartId" class="space-y-4" @submit="onSubmit">
        <UFormField label="Node Reference" name="nodeRef" class="max-w-96" required>
          <USelect
            v-model="selectedChartId"
            value-key="id"
            label-key="name"
            :items="pxCharts"
            class="w-full"
            placeholder="Enter Chart Reference"
          />
        </UFormField>
        <UButton type="submit"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
