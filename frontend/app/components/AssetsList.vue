<script setup lang="ts">
import type { Asset } from '~/utils/movie-script-evaluator'
import type { ColumnDef } from '@tanstack/vue-table'

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
</script>

<template>
  <h4>Total Number of Assets: {{ props.assets.length }}</h4>
  <UTable sticky :data="props.assets" :loading="props.loading" :columns="columns" class="flex-1" />
</template>
