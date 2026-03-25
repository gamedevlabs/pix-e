<script setup lang="ts">
const props = defineProps<{
  namedEntity: Partial<NamedEntity>
  isBeingEdited?: boolean
  showEdit?: boolean
  showDelete?: boolean
  variant?: 'compact'
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<NamedEntity>): void
  (event: 'edit' | 'delete'): void
}>()

const draft = ref({ ...props.namedEntity })

// Helper to check if name is valid
const isValid = computed(() => !!draft.value.name?.trim())

watch(
  () => props.isBeingEdited,
  (newVal) => {
    if (newVal) {
      draft.value = { ...props.namedEntity }
    }
  },
)

function emitEdit() {
  emit('edit')
}

function emitUpdate() {
  if (!isValid.value) return
  emit('update', draft.value)
}

function emitDelete() {
  emit('delete')
}
</script>

<template>
  <UCard
    :class="[
      'w-72 hover:shadow-lg transition',
      variant !== null && variant === 'compact' ? 'min-h-35' : 'min-h-55',
    ]"
    variant="subtle"
  >
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg overflow-hidden text-ellipsis whitespace-nowrap mr-2">
          {{ props.namedEntity.name }}
        </h2>
        <div class="shrink-0">
          <UButton
            v-if="showEdit"
            aria-label="Edit"
            icon="i-lucide-pencil"
            color="primary"
            variant="ghost"
            @click="emitEdit"
          />
          <UButton
            v-if="showDelete"
            aria-label="Delete"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            @click="emitDelete"
          />
        </div>
      </div>

      <div v-else class="header gap-2">
        <UInput
          v-model="draft.name"
          class="grow min-w-0"
          variant="outline"
          placeholder="Enter name here..."
          autofocus
          @keydown.enter.prevent="emitUpdate"
        />
      </div>
    </template>

    <template #default>
      <div v-if="'description' in namedEntity">
        <p v-if="!isBeingEdited" class="text-sm text-gray-500 break-words line-clamp-4">
          {{ namedEntity.description }}
        </p>
        <UTextarea
          v-else
          v-model="draft.description"
          placeholder="Enter description here..."
          size="md"
          variant="outline"
          :rows="3"
          autoresize
          class="w-full"
          @keydown.ctrl.enter="emitUpdate"
        />
      </div>

      <div v-if="!isBeingEdited" class="mt-2">
        <slot name="default" />
      </div>
      <div v-else class="mt-2">
        <slot name="defaultEdit" />
      </div>
    </template>

    <template v-if="isBeingEdited || $slots.footerExtra || $slots.footerExtraEdit" #footer>
      <div v-if="!isBeingEdited">
        <slot name="footerExtra" />
      </div>
      <div v-else class="flex flex-col gap-2">
        <slot name="footerExtraEdit" />
        <div class="flex items-center justify-end gap-2">
          <UButton
            aria-label="Cancel"
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            @click="emitEdit"
          />
          <UButton
            aria-label="Save"
            label="Save"
            icon="i-lucide-check"
            color="primary"
            variant="solid"
            :disabled="!isValid"
            @click="emitUpdate"
          />
        </div>
      </div>
    </template>
  </UCard>
</template>

<style scoped>
.header {
  @apply flex items-center justify-between w-full;
}
</style>
