<script setup lang="ts">
const props = defineProps<{
  chart: PxChart
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'edit' | 'delete' | 'removeNode'): void
  (event: 'addNode', nodeId: string): void
}>()

const draft = ref({ ...props.chart })

const localChart = ref<PxChart>(props.chart)
const isBeingEdited = ref(false)

watch(
  () => isBeingEdited,
  (newVal) => {
    if (newVal) {
      draft.value = { ...props.chart }
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
  <UCard :class="['hover:shadow-lg transition']">
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxcharts-id', params: { id: localChart.id } }">
            {{ localChart.name }}
          </NuxtLink>
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
      <div v-if="'description' in localChart">
        <div v-if="!isBeingEdited">
          <h2>Description</h2>
          <p>{{ localChart.description }}</p>
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
