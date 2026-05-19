<script setup lang="ts">
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()

onMounted(() => {
  fetchPxNodes()
})

const emit = defineEmits<{ close: [string] }>()

const formState = ref({ selectedNodeId: '' })

async function onSubmit() {
  emit('close', formState.value.selectedNodeId)
}
</script>

<template>
  <UModal
    :title="'Add PX node'"
    description="Add PX node from list of already existing node."
  >
    <template #body>
      <UForm :state="formState" class="space-y-4" @submit="onSubmit">
        <UFormField label="Node Reference" name="selectedNodeId" class="max-w-96" required>
          <USelect
            v-model="formState.selectedNodeId"
            value-key="id"
            label-key="name"
            :items="pxNodes"
            class="w-full"
            placeholder="Select Node"
          />
        </UFormField>
        <UButton type="submit"> Add </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
