<script setup lang="ts">
import { NamedEntityCard } from '#components'
const { error } = usePixeToast()

const { createItem: createPxNode } = usePxNodes()

const emit = defineEmits<{ close: [string] }>()

const newItem = ref<NamedEntity>({ name: '', description: '' })

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  if (!newEntityDraft.description) {
    error('Description is required!')
    return
  } else {
    const nodeId = await createPxNode(newEntityDraft)
    emit('close', nodeId)
  }
}

async function onClose() {
  emit('close', '')
}
</script>

<template>
  <UModal
    :title="'Create new PX node:'"
    :close="false"
    :dismissible="false"
    class="w-xs"
    style="padding: -10px"
  >
    <template #body>
      <NamedEntityCard
        :named-entity="newItem"
        :is-being-edited="true"
        style="margin: -10px"
        @edit="onClose()"
        @update="createItem"
      />
    </template>
  </UModal>
</template>

<style scoped></style>
