<script setup lang="ts">
import type { FormError, SelectMenuItem } from '@nuxt/ui'
import { NuxtEmojiPicker } from '#components'

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
})

interface PxKeyDefState {
  name: string
  key_type: PxKeyTypesType | undefined
  consumable: boolean
  fixed: boolean
  unique: boolean
  symbol: string
}

const defaultKeyState: PxKeyDefState = {
  name: '',
  key_type: undefined,
  consumable: false,
  fixed: false,
  unique: false,
  symbol: '🔑',
}

const keyState = ref<PxKeyDefState>({ ...defaultKeyState })

function validateKeyDefInput(state: Partial<PxKeyDefState>): FormError[] {
  const errors = []
  if (!state.name) errors.push({ name: 'name', message: 'Required' })
  if (!state.key_type) errors.push({ name: 'key_type', message: 'Required' })
  return errors
}

async function handleCreateKey() {
  await createPxKeyDefinition({ ...keyState.value })
  keyState.value = defaultKeyState
}

async function handleUpdateKey(updatedDefinition: PxKeyDefinition) {
  await updatePxKeyDefinition(updatedDefinition.id, updatedDefinition)
}

// see https://github.com/delowardev/vue3-emoji-picker/?tab=readme-ov-file#usage
async function onSelectKeyEmoji(emoji) {
  keyState.value.symbol = emoji.i
}

export type PxKeySelectMenuItem = SelectMenuItem & { label: string; value: string }

const keysForUnlockedBySelection: Ref<PxKeySelectMenuItem[]> = computed(() => {
  return pxKeyDefinitions.value.map((def) => ({ label: def.name, value: def.id }))
})

interface PxLockDefState {
  name: string
  soft_gate: boolean
  unlocked_by: string[]
  unlock_mode: PxUnlockModeType
  symbol: string
}

const defaultLockState: PxLockDefState = {
  name: '',
  soft_gate: false,
  unlocked_by: [],
  unlock_mode: 'permanent',
  symbol: '🔒',
}

const lockState = ref<PxLockDefState>({ ...defaultLockState })

function validateLockDefInput(state: Partial<PxLockDefState>): FormError[] {
  const errors = []
  if (!state.name) errors.push({ name: 'name', message: 'Required' })
  if (!state.unlocked_by?.length) errors.push({ name: 'unlocked_by', message: 'Required' })
  return errors
}

async function handleCreateLock() {
  await createPxLockDefinition({ ...lockState.value })
  lockState.value = defaultLockState
}

async function handleUpdateLock(updatedDefinition: PxLockDefinition) {
  await updatePxLockDefinition(updatedDefinition.id, updatedDefinition)
}

// see https://github.com/delowardev/vue3-emoji-picker/?tab=readme-ov-file#usage
async function onSelectLockEmoji(emoji) {
  lockState.value.symbol = emoji.i
}
</script>

<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold mb-6">PxKey Definitions</h1>

      <div class="grid grid-cols-2 gap-16" style="grid-template-columns: 1fr 4fr">
        <UForm
          :state="keyState"
          class="mb-6 space-y-4 p-1"
          :validate="validateKeyDefInput"
          @submit="handleCreateKey"
        >
          <UFormField name="name" required>
            <UInput
              v-model="keyState.name"
              type="text"
              placeholder="Name"
              class="w-full"
              size="lg"
            />
          </UFormField>
          <UFormField label="Type" name="key_type" orientation="horizontal" required>
            <USelectMenu
              v-model="keyState.key_type"
              :items="pxKeyTypesForSelection"
              label-key="label"
              value-key="value"
              placeholder="Select Type"
              :search-input="false"
            />
          </UFormField>
          <UFormField
            label="Consumable"
            orientation="horizontal"
            description="Keys that can only be used once."
          >
            <UCheckbox v-model="keyState.consumable" />
          </UFormField>
          <UFormField
            label="Fixed"
            orientation="horizontal"
            description="Keys that are part of the environment, e.g. levers."
          >
            <UCheckbox v-model="keyState.fixed" />
          </UFormField>
          <UFormField
            label="Unique"
            orientation="horizontal"
            description="Keys that only exist once."
          >
            <UCheckbox v-model="keyState.unique" />
          </UFormField>
          <UFormField name="symbol" label="Symbol" orientation="horizontal">
            <UPopover :enable-touch="false">
              <UButton :label="keyState.symbol" color="neutral" variant="subtle" />

              <template #content>
                <NuxtEmojiPicker :hide-search="false" theme="light" @select="onSelectKeyEmoji" />
              </template>
            </UPopover>
          </UFormField>
          <UButton type="submit" :block="true" class="mt-4">Create PxKey Definition</UButton>
        </UForm>
        <UScrollArea
          v-if="pxKeyDefinitions.length"
          v-slot="{ item }"
          :items="pxKeyDefinitions"
          orientation="horizontal"
          class="w-full"
          :ui="{ viewport: 'gap-8 p-1' }"
        >
          <PxKeyDefinitionCardDetailed
            :definition="item"
            class="min-w-100"
            @edit="handleUpdateKey"
            @delete="deletePxKeyDefinition"
          />
        </UScrollArea>
      </div>
    </div>
    <div class="mt-16">
      <h1 class="text-2xl font-bold mb-6">PxLock Definitions</h1>

      <div class="grid grid-cols-2 gap-16" style="grid-template-columns: 1fr 4fr">
        <UForm
          :state="lockState"
          class="mb-6 space-y-4 p-1"
          :validate="validateLockDefInput"
          @submit="handleCreateLock"
        >
          <UFormField name="name" required>
            <UInput
              v-model="lockState.name"
              type="text"
              placeholder="Name"
              class="w-full"
              size="lg"
            />
          </UFormField>
          <UFormField
            label="Soft Gate"
            orientation="horizontal"
            description="A lock that can also be passed without the key(s), e.g. by skilled players."
          >
            <UCheckbox v-model="lockState.soft_gate" />
          </UFormField>
          <UFormField label="Unlock Mode" orientation="horizontal">
            <USelectMenu
              v-model="lockState.unlock_mode"
              :items="pxUnlockModesForSelection"
              label-key="label"
              value-key="value"
              placeholder="Select Type"
              :search-input="false"
            />
          </UFormField>
          <UFormField name="unlocked_by" label="Unlocked By" orientation="horizontal" required>
            <USelectMenu
              v-model="lockState.unlocked_by"
              :items="keysForUnlockedBySelection"
              :value-key="'value'"
              multiple
              :search-input="false"
              placeholder="Select Keys"
              class="min-w-max"
            />
          </UFormField>
          <UFormField name="symbol" label="Symbol" orientation="horizontal">
            <UPopover :enable-touch="false">
              <UButton :label="lockState.symbol" color="neutral" variant="subtle" />

              <template #content>
                <NuxtEmojiPicker :hide-search="false" theme="light" @select="onSelectLockEmoji" />
              </template>
            </UPopover>
          </UFormField>
          <UButton type="submit" :block="true" class="mt-4">Create PxLock Definition</UButton>
        </UForm>

        <UScrollArea
          v-if="pxLockDefinitions.length"
          v-slot="{ item }"
          :items="pxLockDefinitions"
          orientation="horizontal"
          class="w-full"
          :ui="{ viewport: 'gap-8 p-1' }"
        >
          <PxLockDefinitionCardDetailed
            :definition="item"
            :keys-for-selection="keysForUnlockedBySelection"
            class="min-w-100"
            @edit="handleUpdateLock"
            @delete="deletePxLockDefinition"
          />
        </UScrollArea>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
