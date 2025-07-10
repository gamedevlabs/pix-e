<script setup lang="ts">
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()

onMounted(() => {
  fetchPxNodes()
})

const emit = defineEmits<{ close: [number] }>()

const selectedNodeId = ref(-1)

async function onSubmit() {
  emit('close', selectedNodeId.value)
}
</script>

<template>
  <UModal :title="'Add new Component'">
    <template #body>
      <UForm :state="selectedNodeId" class="space-y-4" @submit="onSubmit">
        <UFormField label="Node Reference" name="nodeRef" class="max-w-96" required>
          <USelect
            v-model="selectedNodeId"
            value-key="id"
            label-key="name"
            :items="pxNodes"
            class="w-full"
            placeholder="Enter Node Reference"
          />
        </UFormField>
        <UButton type="submit"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
