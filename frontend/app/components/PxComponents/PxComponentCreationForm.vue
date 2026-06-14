<script setup lang="ts">
import type { FormError } from '@nuxt/ui'

const props = defineProps<{ selectedNodeId: string }>()

const {
  createItem: createPxComponent,
  items: pxComponents,
  fetchAll: fetchPxComponents,
} = usePxComponents()
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxDefinitions, fetchAll: fetchPxDefinitions } = usePxComponentDefinitions()

onMounted(() => {
  fetchPxNodes()
  fetchPxComponents()
  fetchPxDefinitions()
})

const emit = defineEmits<{
  close: (payload: { nodeId: string; componentId: string }) => void
}>()

interface PxComponentState {
  nodeRef: string
  definitionRef: string | undefined
  stringValue: string | undefined
  numberValue: number | undefined
  booleanValue: false
}

const state = ref({
  nodeRef: props.selectedNodeId,
  definitionRef: undefined,
  stringValue: undefined,
  numberValue: undefined,
  booleanValue: false,
})

function validate(state: Partial<PxComponentState>): FormError[] {
  const errors = []
  if (!state.nodeRef) errors.push({ name: 'nodeRef', message: 'Required' })
  if (!state.definitionRef) errors.push({ name: 'definitionRef', message: 'Required' })
  if (selectedDefinition.value && selectedDefinition.value?.type === 'string' && !state.stringValue)
    errors.push({ name: 'value-string', message: 'Required' })
  if (
    selectedDefinition.value &&
    selectedDefinition.value?.type === 'number' &&
    typeof state.numberValue !== 'number'
  )
    errors.push({ name: 'value-number', message: 'Required' })
  return errors
}

const availableDefinitionsForSelectedNode = computed(() => {
  return pxDefinitions.value.filter(
    (definition) =>
      pxComponents.value.filter(
        (component) =>
          component.node === state.value.nodeRef && component.definition === definition.id,
      ).length === 0,
  )
})

const selectedDefinition = computed(() => {
  if (!availableDefinitionsForSelectedNode.value) {
    return undefined
  }
  return availableDefinitionsForSelectedNode.value
    .filter((def) => def.id === state.value.definitionRef)
    .pop()
})

async function onSubmit() {
  if (!selectedDefinition.value) return

  let enteredValue: number | boolean | string | undefined

  switch (selectedDefinition.value.type) {
    case 'number':
      enteredValue = state.value.numberValue
      break
    case 'boolean':
      enteredValue = state.value.booleanValue
      break
    case 'string':
      enteredValue = state.value.stringValue
      break
    default:
      enteredValue = undefined
  }

  if (enteredValue === undefined) return

  const componentId = await createPxComponent({
    node: state.value.nodeRef,
    definition: state.value.definitionRef,
    value: enteredValue,
  })
  emit('close', { nodeId: state.value.nodeRef, componentId })
}
</script>

<template>
  <UModal :title="'Add new Component'">
    <template #body>
      <UForm :state="state" class="space-y-4" :validate="validate" @submit="onSubmit">
        <UFormField label="Node Reference" name="nodeRef" required>
          <USelectMenu
            v-model="state.nodeRef"
            value-key="id"
            label-key="name"
            :items="pxNodes"
            class="w-full"
            placeholder="Enter Node Reference"
          />
        </UFormField>

        <UFormField label="Definition Reference" name="definitionRef" required>
          <div v-if="availableDefinitionsForSelectedNode.length === 0">
            The selected node already has a component for each definition available.
          </div>
          <USelect
            v-else
            v-model="state.definitionRef"
            value-key="id"
            label-key="name"
            :items="availableDefinitionsForSelectedNode"
            class="w-full"
            placeholder="Select Definition Reference"
          />
        </UFormField>

        <UFormField
          v-if="selectedDefinition && selectedDefinition.type === 'string'"
          label="Value"
          name="value-string"
          required
        >
          <UInput v-model="state.stringValue" placeholder="Enter String Value" class="w-full" />
        </UFormField>
        <UFormField
          v-else-if="selectedDefinition && selectedDefinition.type === 'number'"
          label="Value"
          name="value-number"
          required
        >
          <UInputNumber
            v-model="state.numberValue"
            placeholder="Enter Numeric Value"
            class="w-full"
          />
        </UFormField>
        <UFormField
          v-else-if="selectedDefinition && selectedDefinition.type === 'boolean'"
          label="Value"
          name="value-boolean"
          required
        >
          <UCheckbox
            v-model="state.booleanValue"
            placeholder="Enter Boolean Value"
            class="w-full"
          />
        </UFormField>

        <!--
        <UFormField label="Value" name="value" class="max-w-96" required>
          <div
            v-if="
              !state.definitionRef ||
              !selectedDefinition ||
              availableDefinitionsForSelectedNode.length === 0
            "
          >
            Please select a value type before entering a value.
          </div>
          <div v-else>
            <UInput
              v-if="selectedDefinition!.type === 'string'"
              v-model="state.stringValue"
              required
              placeholder="Enter String Value"
              class="w-full"
            />
            <UInputNumber
              v-else-if="selectedDefinition!.type === 'number'"
              v-model="state.numberValue"
              required
              placeholder="Enter Numeric Value"
              class="w-full"
            />
            <UCheckbox
              v-else-if="selectedDefinition!.type === 'boolean'"
              v-model="state.booleanValue"
              placeholder="Enter Boolean Value"
              class="w-full"
            />
          </div>
        </UFormField>
    -->

        <UButton type="submit" class="mt-4"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
