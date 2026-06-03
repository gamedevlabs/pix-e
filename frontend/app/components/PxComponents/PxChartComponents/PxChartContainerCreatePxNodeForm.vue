<script setup lang="ts">
import { NamedEntityCard } from '#components'

const { createItem: createPxNode } = usePxNodes()
//needed to make sure create node on nodes pages looks correctly??
const { toggleSubstep } = useProjectWorkflow()

const emit = defineEmits<{ close: [string] }>()

const newItem = ref<NamedEntity>({ name: '', description: '' })

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  const nodeId = await createPxNode(newEntityDraft)

  // px-2-2: "Create your first node"
  await toggleSubstep('px-2', 'px-2-2')

  emit('close', nodeId)
}

async function onClose() {
  emit('close', '')
}
</script>

<template>
  <UModal :title="'Create new PX node:'" :close="false" :dismissible="false">
    <template #body>
      <NamedEntityCard
        :named-entity="newItem"
        :is-being-edited="true"
        @edit="onClose()"
        @update="createItem"
      />
    </template>
  </UModal>
</template>

<style scoped></style>
