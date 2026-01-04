<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const {
  items: pxNodes,
  fetchAll: fetchPxNodes,
  createItem: createPxNode,
  deleteItem: deletePxNode,
} = usePxNodes()

onMounted(() => {
  fetchPxNodes()
})

const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  await createPxNode({ ...newEntityDraft })
  newItem.value = null
}

// Not particularly efficient, but works for now.
// Problem is that I do not get the specified PxNodeCard to reload its components from here
async function handleForeignAddComponent() {
  pxNodes.value = []
  await fetchPxNodes()
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Px Nodes</template>

      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="node in pxNodes" :key="node.id">
          <PxNodeCard
            :key="node.id"
            :node-id="node.id"
            :visualization-style="'detailed'"
            @delete="deletePxNode"
            @add-foreign-component="handleForeignAddComponent"
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
