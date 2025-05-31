<script setup lang="ts">
const {
  items: pxNodes,
  fetchAll: fetchPxNodes,
  createItem: createPxNode,
  updateItem: updatePxNode,
  deleteItem: deletePxNode,
} = usePxNodes()

const state = ref({
  name: '',
  description: '',
})

onMounted(() => {
  fetchPxNodes()
})

async function handleCreate() {
  await createPxNode(state.value)
  state.value.name = ''
  state.value.description = ''
}

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)
}

async function handleAddComponent() {
  console.log('AddComponent')
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>
        This is the header
      </template>

      <SimpleCardSection use-add-button @add-clicked="console.log('bois')">
        <div v-for="node in pxNodes" :key="node.id">
          <PxNodeCard
              :node="node"
              @add-component="handleAddComponent"
              @edit="handleUpdate"
              @delete="deletePxNode"
          />
        </div>
      </SimpleCardSection>

    </SimpleContentWrapper>
    <SimpleContentWrapper>
      <template #header>
        This is the header
      </template>

      <SimpleCardSection>
        <div v-for="node in pxNodes" :key="node.id">
          <PxNodeCard
              :node="node"
              @add-component="handleAddComponent"
              @edit="handleUpdate"
              @delete="deletePxNode"
          />
        </div>
      </SimpleCardSection>

    </SimpleContentWrapper>
  </div>
</template>

<style scoped>

</style>