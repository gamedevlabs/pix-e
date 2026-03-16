<script setup lang="ts">
import type { SelectMenuItem } from '@nuxt/ui'

definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Lock and Key Definitions',
    icon: 'i-lucide-book-key',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 5,
    showInNav: true,
  },
})

const {
  items: pxLockDefinitions,
  fetchAll: fetchPxLockDefinitions,
  createItem: createPxLockDefinition,
  updateItem: updatePxLockDefinition,
  deleteItem: deletePxLockDefinition,
} = usePxLockDefinitions()

const {
  items: pxKeyDefinitions,
  fetchAll: fetchPxKeyDefinitions,
  createItem: createPxKeyDefinition,
  updateItem: updatePxKeyDefinition,
  deleteItem: deletePxKeyDefinition,
} = usePxKeyDefinitions()

onMounted(() => {
  fetchPxLockDefinitions()
  fetchPxKeyDefinitions()
  console.log(`Key Definitions: ${pxKeyDefinitions.value.toString()}`)
})

const keyTypes = ref(['item', 'ability'])

interface KeyState {
  name: string
  type: PxKeyTypesType
  consumable: boolean
  fixed: boolean
  unique: boolean
}

const defaultKeyState: KeyState = {
  name: '',
  type: 'none',
  consumable: false,
  fixed: false,
  unique: false,
}

const keyState = ref<KeyState>(defaultKeyState)

async function handleCreateKey() {
  await createPxKeyDefinition({ ...keyState.value })
  keyState.value.name = ''
  keyState.value.type = 'none'
}

async function handleUpdateKey(updatedDefinition: PxKeyDefinition) {
  await updatePxKeyDefinition(updatedDefinition.id, updatedDefinition)
}

const unlockModes = ref(['permanent', 'temporary', 'reversible', 'collapsible'])

export type PxKeySelectMenuItem = SelectMenuItem & { label: string, value: string }

const keysForSelection : Ref<PxKeySelectMenuItem[]> = computed(() => {
  return pxKeyDefinitions.value.map((def) => ({label: def.name, value: def.id}))
})

interface LockState {
  name: string
  unlocked_by: string[]
  unlock_mode: PxLockUnlockModeType
}

const defaultState: LockState = {
  name: '',
  unlocked_by: [],
  unlock_mode: 'permanent',
}

const lockState = ref<LockState>(defaultState)

async function handleCreateLock() {
  //lockState.value.unlockedBy = lockState.value.unlockedBy.map((keyName) => pxKeyDefinitions.value.find((def) => def.name === keyName)!.id)
  await createPxLockDefinition({ ...lockState.value })
  //await createPxKeyDefinition({name: lockState.value.name})
  lockState.value = defaultState
}

async function handleUpdateLock(updatedDefinition: PxLockDefinition) {
  await updatePxLockDefinition(updatedDefinition.id, updatedDefinition)
}
</script>

<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold mb-6">PxKey Definitions</h1>

      <div class="grid grid-cols-2 gap-16" style="grid-template-columns: 1fr 4fr">
        <UForm :state="keyState" class="mb-6 space-y-4 p-1" @submit="handleCreateKey">
          <UFormField>
            <UInput v-model="keyState.name" type="text" placeholder="Name" />
          </UFormField>
          <UFormField label="Type" name="type" orientation="horizontal">
            <USelectMenu v-model="keyState.type" :items="keyTypes" :search-input="false" />
          </UFormField>
          <UFormField label="Consumable" orientation="horizontal" description="Keys that can only be used once.">
            <UCheckbox v-model="keyState.consumable" />
          </UFormField>
          <UFormField label="Fixed" orientation="horizontal" description="Keys that are part of the environment, e.g. levers.">
            <UCheckbox v-model="keyState.fixed" />
          </UFormField>
          <UFormField label="Unique" orientation="horizontal" description="Keys that only exist once.">
            <UCheckbox v-model="keyState.unique"  />
          </UFormField>
          <UButton type="submit" class="bottom-full">Create Key</UButton>
        </UForm>
        <UScrollArea
          v-if="pxKeyDefinitions.length"
          v-slot="{ item }"
          :items="pxKeyDefinitions"
          orientation="horizontal"
          class="w-full data-[orientation=horizontal]:h-96"
          :ui="{ viewport: 'gap-8 p-1' }"
        >
            <PxKeyDefinitionCardDetailed
              :definition="item"
              @edit="handleUpdateKey"
              @delete="deletePxKeyDefinition"
            />
        </UScrollArea>
      </div>
    </div>
    <div class="mt-16">
      <h1 class="text-2xl font-bold mb-6">PxLock Definitions</h1>

      <div class="grid grid-cols-2 gap-16" style="grid-template-columns: 1fr 4fr">
        <UForm :state="lockState" class="mb-6 space-y-4 p-1" @submit="handleCreateLock">
          <UFormField>
            <UInput v-model="lockState.name" type="text" placeholder="Name" />
          </UFormField>
          <UFormField label="Unlock Mode" orientation="horizontal">
            <USelectMenu v-model="lockState.unlock_mode" :items="unlockModes" :search-input="false" />
          </UFormField>
          <UFormField label="Unlocked By" orientation="horizontal">
            <USelectMenu v-model="lockState.unlocked_by" :items="keysForSelection" :value-key="'value'" multiple :search-input="false" placeholder="Select Keys" />
          </UFormField>
          <UButton type="submit">Create Lock</UButton>
        </UForm>

        <UScrollArea
          v-if="pxLockDefinitions.length"
          v-slot="{ item }"
          :items="pxLockDefinitions"
          orientation="horizontal"
          class="w-full data-[orientation=horizontal]:h-96"
          :ui="{ viewport: 'gap-8 p-1' }"
        >
          <PxLockDefinitionCardDetailed
              :definition="item"
              :keys-for-selection="keysForSelection"
              @edit="handleUpdateLock"
              @delete="deletePxLockDefinition"
            />
        </UScrollArea>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
