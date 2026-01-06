<script setup lang="ts">
import type { Asset } from '~/utils/movie-script-evaluator'
import type { ColumnDef } from '@tanstack/vue-table'
import { ref, computed } from 'vue'

const props = defineProps<{
  assets: Asset[]
  loading?: boolean
}>()

const columns: ColumnDef<Asset>[] = [
  {
    accessorKey: 'name',
    header: 'Asset Name',
  },
  {
    accessorKey: 'class_name',
    header: 'UClass Name',
  },
  {
    accessorKey: 'path',
    header: 'Asset Path',
  },
]

const searchQuery = ref('')

const filteredAssets = computed(() => {
  if (!searchQuery.value) return props.assets
  return props.assets.filter((asset: Asset) =>
    asset.name?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})
</script>


<template>
  <div class="flex items-center space-x-4 mb-4">
    <h4>Total Number of Assets: {{ props.assets.length }}</h4>
    <UInput
      v-model="searchQuery"
      placeholder="Search Assets by Name"
      class="w-64"
    />
  </div>
  <UTable sticky :data="filteredAssets" :loading="props.loading" :columns="columns" class="flex-1" />
</template>
