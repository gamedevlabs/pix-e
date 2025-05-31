<script setup lang="ts">
const props = defineProps<{ selectedNodeId: number }>()

const { createItem: createPxComponent } = usePxComponents()
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxDefinitions, fetchAll: fetchPxDefinitions } = usePxComponentDefinitions()
const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()

onMounted(() => {
  fetchPxNodes()
  fetchPxComponents()
  fetchPxDefinitions()
})

const emit = defineEmits<{ close: [boolean] }>()

const state = ref({
  nodeRef: props.selectedNodeId,
  definitionRef: undefined,
  value: undefined,
})

async function onSubmit() {
  await createPxComponent({
    node: state.value.nodeRef,
    definition: state.value.definitionRef,
    value: state.value.value,
  })
  emit('close', true)
}
</script>

<template>
  <UModal :title="'Add new Component'">
    <template #body>
      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <UFormField label="Node Reference" name="nodeRef" class="max-w-96" required>
          <USelect
            v-model="state.nodeRef"
            value-key="id"
            label-key="name"
            :items="pxNodes"
            class="w-full"
            placeholder="Enter Node Reference"
          />
        </UFormField>

        <UFormField label="Definition Reference" name="definitionRef" class="max-w-96" required>
          <USelect
            v-model="state.definitionRef"
            value-key="id"
            label-key="name"
            :items="
              pxDefinitions.filter(
                (definition) =>
                  pxComponents.filter(
                    (component) =>
                      component.node === state.nodeRef && component.definition === definition.id,
                  ).length === 0,
              )
            "
            class="w-full"
            placeholder="Select Definition Reference"
          />
        </UFormField>

        <UFormField label="Value" name="value" class="max-w-96" required>
          <div v-if="!state.definitionRef">Please select a value type before entering a value.</div>
          <div v-else>
            <UInput
              v-if="
                pxDefinitions.filter((def) => def.id === state.definitionRef).pop()?.type ===
                'string'
              "
              v-model="state.value"
              required
              placeholder="Enter String Value"
              class="w-full"
            />
            <UInputNumber
              v-else-if="
                pxDefinitions.filter((def) => def.id === state.definitionRef).pop()?.type ===
                'number'
              "
              v-model="state.value"
              required
              placeholder="Enter Numeric Value"
              class="w-full"
            />
            <UCheckbox
              v-else-if="
                pxDefinitions.filter((def) => def.id === state.definitionRef).pop()?.type ===
                'boolean'
              "
              v-model="state.value"
              placeholder="Enter Boolean Value"
              class="w-full"
            />
          </div>
        </UFormField>

        <UButton type="submit"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
