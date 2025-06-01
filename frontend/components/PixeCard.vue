<script setup lang="ts">
const props = defineProps<{
  namedEntity: NamedEntity
  isBeingEdited: boolean
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: NamedEntity): void
  (event: 'edit' | 'delete'): void
}>()

const draft = ref({ ...props.namedEntity })

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
  emit('update', draft.value)
}

function emitDelete() {
  emit('delete')
}
</script>

<template>
  <UCard class="w-72 min-h-55 hover:shadow-lg transition" variant="subtle">
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg">
          {{ props.namedEntity.name }}
        </h2>
        <div>
          <UButton
            aria-label="Edit"
            icon="i-lucide-pencil"
            color="primary"
            variant="ghost"
            @click="emitEdit"
          />
          <UButton
            aria-label="Delete"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            @click="emitDelete"
          />
        </div>
      </div>

      <div v-else class="header">
        <UInput v-model="draft.name" class="max-w-44" variant="subtle" placeholder="Enter name here..."/>
        <div>
          <UButton
            aria-label="Edit"
            icon="i-lucide-save"
            color="primary"
            variant="ghost"
            @click="emitUpdate"
          />
          <UButton
            aria-label="Delete"
            icon="i-lucide-x"
            color="error"
            variant="ghost"
            @click="emitEdit"
          />
        </div>
      </div>
    </template>

    <template #default>
      <p v-if="!isBeingEdited">{{ namedEntity.description }}</p>
      <UTextarea
        v-else
        v-model="draft.description"
        placeholder="Enter description here..."
        size="lg"
        variant="subtle"
        :rows="1"
        autoresize
        class="w-full"
      />

      <div v-if="!isBeingEdited">
        <slot name="defaultExtra" />
      </div>
      <div v-else>
        <slot name="defaultExtraEdit" />
      </div>
    </template>

    <template v-if="$slots.footerExtra || $slots.footerExtraEdit" #footer>
      <div v-if="!isBeingEdited">
        <slot name="footerExtra" />
      </div>
      <div v-else>
        <slot name="footerExtraEdit" />
      </div>
    </template>
  </UCard>
</template>

<style scoped>
.header {
  @apply flex items-center justify-between w-full;
}
</style>
