<script lang="ts" setup>
import type { RequiredAsset } from '~/utils/movie-script-evaluator'
import type { ColumnDef } from '@tanstack/vue-table'

const columns: ColumnDef<RequiredAsset>[] = [
  { accessorKey: 'name', header: 'Asset Name' },
  { accessorKey: 'purpose', header: 'Asset Type' },
  { accessorKey: 'description', header: 'Description' },
]

const props = defineProps<{
  requiredAssets?: RequiredAsset[]
}>()

const items = ref<RequiredAsset[]>([...(props.requiredAssets || [])])
</script>

<template>
  <UCard>
    <template #header>
      <h2 class="text-lg font-semibold">Recommended Assets</h2>
    </template>

    <UTable :columns="columns" :data="items" />
  </UCard>
</template>
