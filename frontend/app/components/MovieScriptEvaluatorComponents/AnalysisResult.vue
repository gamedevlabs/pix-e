<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import type { ScriptSceneAnalysis } from '~/utils/movie-script-evaluator'
import type { TableRow } from '@nuxt/ui'

/**
 * Table columns
 */
const columns: ColumnDef<ScriptSceneAnalysis>[] = [
  { accessorKey: 'scene', header: 'Scene' },
  { accessorKey: 'asset_name', header: 'Asset Name' },
  { accessorKey: 'asset_type', header: 'Asset Type' },
  { accessorKey: 'fab_search_keyword', header: 'FAB Keyword' },
  { accessorKey: 'notes', header: 'Notes' },
]

const props = defineProps<{
  analysisData?: ScriptSceneAnalysis[]
}>()

const isAnyItemChanged = ref(false)

const emit = defineEmits<{
  (e: 'save-all', items: ScriptSceneAnalysis[]): void
  (e: 'load-items'): void
}>()

/**
 * Local state (would come from backend)
 */
const items = ref<ScriptSceneAnalysis[]>([...(props.analysisData || [])])

const emptyForm = (): ScriptSceneAnalysis => ({
  scene: '',
  asset_name: '',
  asset_type: '',
  fab_search_keyword: '',
  notes: '',
})

const form = reactive<ScriptSceneAnalysis>(emptyForm())
const editingIndex = ref<number | null>(null)

/**
 * Add / Update
 */
function saveItem() {
  if (editingIndex.value === null) {
    items.value.push({ ...form })
  } else {
    items.value[editingIndex.value] = { ...form }
  }

  isAnyItemChanged.value = true

  resetForm()
}

/**
 * Edit row
 */
function editItem(index: number) {
  Object.assign(form, items.value[index])
  editingIndex.value = index
}

/**
 * Delete row
 */
function deleteItem(index: number) {
  items.value.splice(index, 1)

  if (editingIndex.value === index) {
    resetForm()
  }

  isAnyItemChanged.value = true
}

/**
 * Cancel edit
 */
function cancelEdit() {
  resetForm()
}

function resetForm() {
  Object.assign(form, emptyForm())
  editingIndex.value = null
}

function select(item: TableRow<ScriptSceneAnalysis>) {
  const index = item.index
  editItem(index)
}

function saveChanges() {
  // Here you would typically send the `items` data to your backend API
  emit('save-all', items.value)
  emit('load-items')
  isAnyItemChanged.value = false
}

function discardChanges() {
  const filteredProps = props.analysisData?.filter(item => item.id !== undefined && item.id !== null)
  items.value = [...(filteredProps || [])]
  isAnyItemChanged.value = false
  resetForm()
  emit('load-items')
}

function isAllItemsHaveId() {
  return items.value.every((item) => item.id !== undefined && item.id !== null)
}
</script>

<template>
  <UCard>
    <template #header>
      <h2 class="text-lg font-semibold">Scene Analysis</h2>
    </template>

    <!-- Add / Edit Form -->
    <div class="grid grid-cols-5 gap-2 mb-4">
      <UInput v-model="form.scene" placeholder="Scene" />
      <UInput v-model="form.asset_name" placeholder="Asset Name" />
      <UInput v-model="form.asset_type" placeholder="Asset Type" />
      <UInput v-model="form.fab_search_keyword" placeholder="FAB Keyword" />
      <UInput v-model="form.notes" placeholder="Notes" />
    </div>

    <div class="flex gap-2 mb-6">
      <UButton color="primary" @click="saveItem">
        {{ editingIndex !== null ? 'Update' : 'Add' }}
      </UButton>

      <UButton
        v-if="editingIndex !== null"
        color="error"
        variant="soft"
        @click="deleteItem(editingIndex!)"
      >
        Delete
      </UButton>

      <UButton v-if="editingIndex !== null" color="info" variant="soft" @click="cancelEdit">
        Cancel
      </UButton>
    </div>

    <!-- Table -->
    <UTable :columns="columns" :data="items" @select="select" />
    <div class="flex gap-2 mt-6 align-right justify-end">

      <UButton
      v-if="!isAllItemsHaveId() || isAnyItemChanged"
      color="success"
      label="Save Results"
      @click="saveChanges"
      />
      
      <UButton
      v-if="!isAllItemsHaveId() || isAnyItemChanged"
      color="error"
      label="Discard Changes"
      @click="discardChanges"
      />
    </div>
  </UCard>
</template>
