<script setup lang="ts">
const { pxnodes, loading, fetchPxNodes, createPxNode, updatePxNode, deletePxNode } = usePxNodes()

const form = ref({
  name: '',
  description: '',
})

const editingNode = ref<PxNode | null>(null)
const editForm = ref({
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

function startEdit(node: PxNode) {
  editingNode.value = node
  editForm.value.name = node.name
  editForm.value.description = node.description
}

async function handleUpdate() {
  if (!editingNode.value) return
  await updatePxNode(editingNode.value.id, editForm.value)
  editingNode.value = null
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
      <UCard v-for="node in pxnodes" :key="node.id" class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">{{ node.name }}</h2>
        </template>
        <p>{{ node.description }}</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="secondary" variant="soft" @click="startEdit(node)">Edit</UButton>
            <UButton color="error" variant="soft" @click="deletePxNode(node.id)">Delete</UButton>
          </div>
        </template>
      </UCard>
    </section>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="node in pxnodes" :key="node.id">
        <PxNodeCard :node="node"/>
      </div>
    </section>

    <!-- Edit Modal -->
    <div
      v-if="editingNode"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white p-6 rounded-lg w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Edit Node</h2>
        <form class="space-y-4" @submit.prevent="handleUpdate">
          <UInput
            v-model="editForm.name"
            type="text"
            placeholder="Name"
            class="input input-bordered w-full"
          />
          <UTextarea
            v-model="editForm.description"
            placeholder="Description"
            class="textarea textarea-bordered w-full"
          />
          <div class="flex justify-end gap-2">
            <UButton type="button" @click="editingNode = null">Cancel</UButton>
            <UButton type="submit">Save</UButton>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
