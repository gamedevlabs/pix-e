<script setup lang="ts">
const props = defineProps<{
  pxChart: Partial<PxChart>
  isBeingEdited?: boolean
  showEdit?: boolean
  showDelete?: boolean
  variant?: 'compact'
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'edit' | 'delete'): void
}>()

const draft = ref({ ...props.pxChart })

watch(
  () => props.isBeingEdited,
  (newVal) => {
    if (newVal) {
      draft.value = { ...props.pxChart }
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
  <UCard
    :class="[
      'w-72 hover:shadow-lg transition',
      variant !== null && variant === 'compact' ? 'min-h-35' : 'min-h-55',
    ]"
    variant="subtle"
  >
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxcharts-id', params: { id: props.pxChart.id } }">
            {{ props.pxChart.name }}
          </NuxtLink>
        </h2>
        <div>
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

      <div v-else class="header">
        <UInput
          v-model="draft.name"
          class="max-w-44"
          variant="subtle"
          placeholder="Enter name here..."
        />
        <div>
          <UButton
            aria-label="Update"
            icon="i-lucide-save"
            color="primary"
            variant="ghost"
            @click="emitUpdate"
          />
          <UButton
            aria-label="Cancel"
            icon="i-lucide-x"
            color="error"
            variant="ghost"
            @click="emitEdit"
          />
        </div>
      </div>
    </template>

    <template #default>
      <div v-if="'description' in pxChart">
        <p v-if="!isBeingEdited">{{ pxChart.description }}</p>
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
      </div>

      <div v-if="!isBeingEdited">
        <slot name="default" />
      </div>
      <div v-else>
        <slot name="defaultEdit" />
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
