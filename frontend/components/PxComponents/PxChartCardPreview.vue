<script setup lang="ts">
const props = defineProps<{
  chart: PxChart
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'edit' | 'delete', graphId: string): void
}>()

const draft = ref({ ...props.chart })

const isBeingEdited = ref(false)

watch(
  () => isBeingEdited.value,
  (newVal) => {
    if (newVal) {
      draft.value = { ...props.chart }
    }
  },
)

function startEdit() {
  isBeingEdited.value = true
}

function confirmEdit() {
  emit('update', { ...props.chart, ...draft.value })
  isBeingEdited.value = false
}

function cancelEdit() {
  isBeingEdited.value = false
  draft.value.name = props.chart.name
}

function emitDelete() {
  emit('delete', props.chart.id)
}
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxcharts-id', params: { id: props.chart.id } }">
            {{ props.chart.name }}
          </NuxtLink>
        </h2>
        <div>
          <UButton
            aria-label="Edit"
            icon="i-lucide-pencil"
            color="primary"
            variant="ghost"
            @click="startEdit"
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
            @click="confirmEdit"
          />
          <UButton
            aria-label="Cancel"
            icon="i-lucide-x"
            color="error"
            variant="ghost"
            @click="cancelEdit"
          />
        </div>
      </div>
    </template>

    <template #default>
      <div v-if="'description' in props.chart">
        <div v-if="!isBeingEdited">
          <h2 class="font-semibold text-lg">Description</h2>
          <p>{{ props.chart.description }}</p>
        </div>
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
  </UCard>
</template>

<style scoped>
.header {
  @apply flex items-center justify-between w-full;
}
</style>
