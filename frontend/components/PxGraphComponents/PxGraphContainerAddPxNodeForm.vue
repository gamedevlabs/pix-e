<script setup lang="ts">
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()

onMounted(() => {
  fetchPxNodes()
})

const emit = defineEmits<{ close: [string] }>()

const formState = ref({selectedNodeId: ""})

async function onSubmit() {
  emit('close', formState.value.selectedNodeId)
}
</script>

<template>
  <UModal :title="'Add new PX node'" description="Use this modal to add a PX node to a PX container">
    <template #body>
      <UForm :state="formState" class="space-y-4" @submit="onSubmit">
        <UFormField label="Node Reference" name="selectedNodeId" class="max-w-96" required>
          <USelect
            v-model="formState.selectedNodeId"
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
