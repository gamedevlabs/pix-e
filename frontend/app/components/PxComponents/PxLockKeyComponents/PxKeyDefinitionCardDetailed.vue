<script setup lang="ts">
const props = defineProps<{
  definition: PxKeyDefinition
}>()

const emit = defineEmits<{
  (e: 'edit', updatedDefinition: PxKeyDefinition): void
  (e: 'delete', id: string): void
}>()

const isBeingEdited = ref(false)

type EditableKeyDefinition = Pick<
  PxKeyDefinition,
  'name' | 'key_type' | 'consumable' | 'fixed' | 'unique'
>

const editForm: Ref<EditableKeyDefinition> = ref({
  name: props.definition.name,
  key_type: props.definition.key_type,
  consumable: props.definition.consumable,
  fixed: props.definition.fixed,
  unique: props.definition.unique,
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
  editForm.value = { ...props.definition }
}

function emitDelete() {
  emit('delete', props.definition.id)
}
</script>
<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <div class="flex items-center gap-2">
        🔑
        <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxkeydefinitions-id', params: { id: props.definition.id } }">
            {{ props.definition.name }}
          </NuxtLink>
        </h2>
        <UTextarea v-else v-model="editForm.name" :rows="1" size="lg" />
      </div>
    </template>

    <template #default>
      <div v-if="!isBeingEdited" class="grid grid-cols-2 gap-6">
        <b>Type</b>
        {{ pxKeyTypesDisplayNames[definition.key_type] }}
        <b>Consumable</b>
        <!--
            this is a bit unclean as the value should be based on props.definition, 
            however props should not be used as v-model 
        -->
        <UCheckbox v-model="editForm.consumable" :disabled="true" color="neutral" />
        <b>Fixed</b>
        <UCheckbox v-model="editForm.fixed" :disabled="true" color="neutral" />
        <b>Unique</b>
        <UCheckbox v-model="editForm.unique" :disabled="true" color="neutral" />
      </div>
      <div v-else class="grid grid-cols-2 gap-6">
        <b>Type</b>
        <USelect
          v-model="editForm.key_type"
          :items="pxKeyTypesForSelection"
          label-key="label"
          value-key="value"
        />
        <b>Consumable</b>
        <UCheckbox v-model="editForm.consumable" />
        <b>Fixed</b>
        <UCheckbox v-model="editForm.fixed" />
        <b>Unique</b>
        <UCheckbox v-model="editForm.unique" />
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
