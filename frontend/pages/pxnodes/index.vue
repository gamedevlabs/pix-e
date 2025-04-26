<script setup lang="ts">
import { ref, onMounted } from 'vue'

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
      <UButton type="submit" class="btn btn-primary">Create Node</UButton>
    </form>

    <!-- List of Px Nodes -->
    <div v-if="loading">Loading...</div>
    <div v-else class="grid gap-4">
      <div v-for="node in pxnodes" :key="node.id" class="card p-4 shadow">
        <div class="flex justify-between items-center">
          <div>
            <NuxtLink
              :to="`/pxnodes/${node.id}`"
              class="font-semibold text-lg text-blue-500 hover:underline"
            >
              {{ node.name }}
            </NuxtLink>
            <p class="text-sm text-gray-500">{{ node.description }}</p>
          </div>
          <div class="flex gap-2">
            <UButton class="btn btn-outline btn-sm" @click="startEdit(node)">Edit</UButton>
            <UButton class="btn btn-error btn-sm" @click="deletePxNode(node.id)">Delete</UButton>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div
      v-if="editingNode"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white p-6 rounded-lg w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Edit Node</h2>
        <form class="space-y-4" @submit.prevent="handleUpdate">
          <input
            v-model="editForm.name"
            type="text"
            placeholder="Name"
            class="input input-bordered w-full"
          />
          <textarea
            v-model="editForm.description"
            placeholder="Description"
            class="textarea textarea-bordered w-full"
          />
          <div class="flex justify-end gap-2">
            <button type="button" class="btn" @click="editingNode = null">Cancel</button>
            <button type="submit" class="btn btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
