<script setup lang="ts">
import { PxChartContainerAddPxNodeForm } from '#components'

const props = defineProps<{
  chart: PxChart
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<PxChart>): void
  (event: 'edit' | 'delete' | 'removeNode', graphId: string): void
  (event: 'addNode', graphId: string, nodeId: string): void
}>()

const { updateItem: updatePxChart } = usePxCharts()

const draft = ref({ ...props.chart })

const localChart = ref<PxChart>(props.chart)
const isBeingEdited = ref(false)

const overlay = useOverlay()
const modalAddPxNode = overlay.create(PxChartContainerAddPxNodeForm)

watch(
  () => isBeingEdited,
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
  emit('delete', localChart.value.id)
}

async function emitAddNode() {
  const nodeId = await modalAddPxNode.open().result

  if (!nodeId) return

  await updatePxChart(localChart.value.id!, { associatedNode: nodeId })

  localChart.value.associatedNode = nodeId

  emit('addNode', localChart.value.id, nodeId)
}

async function emitRemoveNode() {
  await updatePxChart(localChart.value.id!, { associatedNode: null })

  localChart.value.associatedNode = undefined

  emit('removeNode', localChart.value.id)
}
</script>

<template>
  <UCard :class="['hover:shadow-lg transition']">
    <template #header>
      <div v-if="!isBeingEdited" class="header">
        <h2 class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxcharts-id', params: { id: localChart.id } }">
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
      <div v-if="'description' in localChart">
        <div v-if="!isBeingEdited">
          <h2 class="font-semibold text-lg mb-2">Description</h2>
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
        <br />
      </div>

      <div v-if="localChart.associatedNode">
        <h2 class="font-semibold text-lg mb-2">Associated Node</h2>
        <PxNodeCard :node-id="localChart.associatedNode!" :visualization-style="'preview'" />
      </div>
      <div v-else>
        <h2 class="italic">No node associated to this chart</h2>
      </div>

      <div v-if="!isBeingEdited">
        <slot name="default" />
      </div>
      <div v-else>
        <slot name="defaultEdit" />
      </div>
    </template>

    <template #footer>
      <slot name="footerExtra">
        <div v-if="localChart.associatedNode">
          <UButton @click="emitRemoveNode">Remove PxNode</UButton>
        </div>
        <div v-else>
          <UButton @click="emitAddNode">Add PxNode</UButton>
        </div>
      </slot>
    </template>
  </UCard>
</template>

<style scoped>
.header {
  @apply flex items-center justify-between w-full;
}
</style>
