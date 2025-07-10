<script setup lang="ts">
import { v4 } from 'uuid'

definePageMeta({
  middleware: 'authentication',
})

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
  const newUuid = v4()
  await createPxNode({id: newUuid, ...state.value})
  state.value.name = ''
  state.value.description = ''
}

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)
}

// Not particularly efficient, but works for now.
// Problem is that I do not get the specified PxNodeCard to reload its components from here
async function handleForeignAddComponent() {
  pxNodes.value = []
  await fetchPxNodes()
}
</script>

<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-6">Px Nodes</h1>

    <!-- Create Form -->
    <UForm :state="state" class="mb-6 space-y-4" @submit.prevent="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" />
      </UFormField>

      <UFormField>
        <UTextarea v-model="state.description" placeholder="Description" class="w-full xl:w-1/2" />
      </UFormField>

      <UButton type="submit">Create Node</UButton>
    </UForm>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <PxNodeCard
        v-for="node in pxNodes"
        :key="node.id"
        :node="node"
        :visualization-style="'detailed'"
        @edit="handleUpdate"
        @delete="deletePxNode"
        @add-foreign-component="handleForeignAddComponent"
      />
    </section>
  </div>
</template>
