<script setup lang="ts">
const { pxnodes, fetchPxNodes, createPxNode, updatePxNode, deletePxNode } = usePxNodes()

const form = ref({
  name: '',
  description: '',
})

onMounted(() => {
  fetchPxNodes()
})

async function handleCreate() {
  await createPxNode(form.value)
  form.value.name = ''
  form.value.description = ''
}

async function handleUpdate(updatedNode: PxNode) {
  await updatePxNode(updatedNode.id, updatedNode)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Px Nodes</h1>

    <!-- Create Form -->
    <form class="mb-6 space-y-4" @submit.prevent="handleCreate">
      <UInput
        v-model="form.name"
        type="text"
        placeholder="Name"
        class="input input-bordered w-full"
      />
      <UTextarea
        v-model="form.description"
        placeholder="Description"
        class="textarea textarea-bordered w-full"
      />
      <UButton type="submit">Create Node</UButton>
    </form>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="node in pxnodes" :key="node.id">
        <PxNodeCard :node="node" @edit="handleUpdate" @delete="deletePxNode" />
      </div>
    </section>
  </div>
</template>
