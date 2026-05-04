<script setup lang="ts">
import type { PxKeySelectMenuItem } from '~/pages/pxlockkeydefinitions.vue'

const props = defineProps<{
  definition: PxLockDefinition
  keysForSelection: PxKeySelectMenuItem[]
}>()

const emit = defineEmits<{
  (e: 'edit', updatedDefinition: PxLockDefinition): void
  (e: 'delete', id: string): void
}>()

const isBeingEdited = ref(false)

type EditableLockDefinition = Pick<
  PxLockDefinition,
  'name' | 'unlocked_by' | 'unlock_mode' | 'soft_gate'
>

const editForm: Ref<EditableLockDefinition> = ref({
  name: props.definition.name,
  unlock_mode: props.definition.unlock_mode,
  unlocked_by: props.definition.unlocked_by,
  soft_gate: props.definition.soft_gate,
})

function startEdit() {
  isBeingEdited.value = true
}

function confirmEdit() {
  isBeingEdited.value = false
  emit('edit', { ...props.definition, ...editForm.value })
}

function cancelEdit() {
  isBeingEdited.value = !isBeingEdited.value
  editForm.value = props.definition
}

function emitDelete() {
  emit('delete', props.definition.id)
}

const unlockModes = ref(['permanent', 'temporary', 'reversible', 'collapsible'])

const unlockedByKeyNames = computed(() => {
  return props.keysForSelection
    .filter((key) => props.definition.unlocked_by.includes(key.value))
    .map((key) => key.label)
})
</script>
<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <div class="flex items-center gap-2">
        🔒
        <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxlockdefinitions-id', params: { id: props.definition.id } }">
            {{ props.definition.name }}
          </NuxtLink>
        </h2>
        <UTextarea v-else v-model="editForm.name" :rows="1" size="lg" />
      </div>
    </template>

    <template #default>
      <div v-if="!isBeingEdited" class="grid grid-cols-2 gap-6">
        <b>Soft Gate</b>
        <UCheckbox v-model="editForm.soft_gate" :disabled="true" color="neutral" />
        <b>Unlock Mode</b>
        {{ definition.unlock_mode }}
        <b>Unlocked By</b>
        <ul>
          <li v-for="name in unlockedByKeyNames" :key="name">{{ name }}</li>
        </ul>
      </div>
      <div v-else class="grid grid-cols-2 gap-6">
        <b>Soft Gate</b>
        <UCheckbox v-model="editForm.soft_gate" />
        <b>Unlock Mode</b>
        <USelect v-model="editForm.unlock_mode" :items="unlockModes" />
        <b>Unlocked By</b>
        <USelectMenu
          v-model="editForm.unlocked_by"
          :items="keysForSelection"
          :value-key="'value'"
          multiple
        />
      </div>
    </template>

    <template #footer>
      <div v-if="!isBeingEdited" class="flex flex-wrap justify-end gap-2">
        <UButton color="secondary" variant="soft" @click="startEdit">Edit</UButton>
        <UButton color="error" variant="soft" @click="emitDelete">Delete</UButton>
      </div>
      <div v-else class="flex gap-2">
        <UButton color="error" variant="soft" @click="cancelEdit">Cancel</UButton>
        <UButton color="secondary" variant="soft" @click="confirmEdit">Confirm</UButton>
      </div>
    </template>
  </UCard>
</template>
<style scoped></style>
