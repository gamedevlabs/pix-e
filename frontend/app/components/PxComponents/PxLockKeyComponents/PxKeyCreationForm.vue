<script setup lang="ts">
import type { FormError } from '@nuxt/ui'

const props = defineProps<{ selectedNodeId: string }>()

const { createItem: createPxKey, items: pxKeys, fetchAll: fetchPxKeys } = usePxKeys()
const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

onMounted(() => {
  fetchPxNodes()
  fetchPxKeys()
  fetchPxKeyDefinitions()
})

const emit = defineEmits<{
  close: (payload: { nodeId: string; keyId: string }) => void
}>()

interface PxKeyState {
  nodeRef: string
  definitionRef: string | undefined
  count: number
}

const state: Ref<PxKeyState> = ref({
  nodeRef: props.selectedNodeId,
  definitionRef: undefined,
  count: 1,
})

function validate(state: Partial<PxKeyState>): FormError[] {
  const errors = []
  if (!state.definitionRef) errors.push({ name: 'definitionRef', message: 'Required' })
  return errors
}

const availableDefinitionsForSelectedNode = computed(() => {
  return pxDefinitions.value.filter(
    (definition) =>
      pxKeys.value.filter(
        (pxkey) => pxkey.node === state.value.nodeRef && pxkey.definition === definition.id,
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

  const enteredValue = state.value.count

  if (enteredValue === undefined) return

  const keyId: string = await createPxKey({
    node: state.value.nodeRef,
    definition: state.value.definitionRef,
    count: enteredValue,
  })
  emit('close', { nodeId: state.value.nodeRef, keyId })
}
</script>

<template>
  <UModal :title="'Add new PxKey'">
    <template #body>
      <UForm :state="state" :validate="validate" class="space-y-4" @submit="onSubmit">
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
            The selected node already has a key for each definition available.
          </div>
          <USelectMenu
            v-else
            v-model="state.definitionRef"
            value-key="id"
            label-key="name"
            :items="availableDefinitionsForSelectedNode"
            class="w-full"
            placeholder="Select Definition Reference"
          />
        </UFormField>

        <UFormField label="Count" name="count">
          <div>
            <UInputNumber
              v-model="state.count"
              :default-value="1"
              placeholder="Key Count"
              class="w-full"
              :min="1"
            />
          </div>
        </UFormField>

        <UButton type="submit" class="mt-4"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
