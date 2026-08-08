<script setup lang="ts">
import { h, resolveComponent } from 'vue'
import type { TableColumn } from '@nuxt/ui'

const UCheckbox = resolveComponent('UCheckbox')

const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()
const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

onMounted(() => {
  fetchPxLockDefinitions()
  fetchPxKeyDefinitions()
})

const items = [
  {
    label: 'Locks',
    icon: 'i-lucide-lock',
    slot: 'locks',
  },
  {
    label: 'Keys',
    icon: 'i-lucide-key',
    slot: 'keys',
  },
]

interface LockDef4User {
  symbol: string
  name: string
  unlockedBy: string
}

const pxLockDefsLegend = computed(() => {
  return pxLockDefinitions.value.map((def) => ({
    symbol: def.symbol,
    name: def.name,
    unlockedBy: def.unlocked_by
      .map((keyDef) => pxKeyDefinitions.value.find((kd) => kd.id === keyDef)!.name)
      .join(', '),
  }))
})

const lockColumns: TableColumn<LockDef4User>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'unlockedBy',
    header: 'Unlocked By',
  },
]

interface KeyDef4User {
  symbol: string
  name: string
  consumable: boolean
  keyType: PxKeyTypesType
}

const pxKeyDefsLegend = computed(() => {
  return pxKeyDefinitions.value.map((def) => ({
    symbol: def.symbol,
    name: def.name,
    consumable: def.consumable,
    keyType: def.key_type,
  }))
})

const keyColumns: TableColumn<KeyDef4User>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'consumable',
    header: 'Consumable',
    cell: ({ row }) => {
      return h(UCheckbox, {
        modelValue: row.getValue('consumable'),
        color: 'neutral',
        disabled: true,
      })
    },
  },
  {
    accessorKey: 'keyType',
    header: 'Key Type',
    cell: ({ row }) => {
      return pxKeyTypesDisplayNames[row.getValue('keyType')]
    },
  },
]
</script>
<template>
  <UPopover
    :content="{
      align: 'end',
      side: 'top',
      sideOffset: 8,
    }"
    :dismissible="false"
  >
    <UButton icon="lucide-book-key" class="m-2" />

    <template #content>
      <UCard title="Definitions Legend">
        <UTabs :items="items">
          <template #locks>
            <UTable :data="pxLockDefsLegend" :columns="lockColumns" class="flex-1" />
          </template>

          <template #keys>
            <UTable :data="pxKeyDefsLegend" :columns="keyColumns" class="flex-1" />
          </template>
        </UTabs>
      </UCard>
    </template>
  </UPopover>
</template>
