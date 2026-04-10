<script setup lang="ts">
import { UInputNumber } from '#components'

const props = defineProps<{ selectedEdge: PxChartEdge; chartId: string }>()

const {
  createItem: createPxLock,
  updateItem: updatePxLock,
  deleteItem: deletePxLock,
  fetchAll: fetchPxLocks,
  items: pxLocks,
} = usePxLocks(props.chartId)
const { items: pxLockDefinitions, fetchAll: fetchPxLockDefinitions } = usePxLockDefinitions()

onMounted(() => {
  fetchPxLocks()
  fetchPxLockDefinitions()
  initialize()
})

export interface LockInfo {
  defId: string
  defName: string
  currentCount: number
  newCount: number
  lockId: string | undefined
}

const emit = defineEmits<{
  close: (payload: { edgeId: string }) => void
}>()

function getNameFromDefinitionId(defId: string) {
  return pxLockDefinitions.value.find((def) => def.id === defId)!.name
}

const state: Ref<Record<string, LockInfo>> = ref({})

async function initialize() {
  await fetchPxLocks()
  //console.log('initializing state...')

  pxLockDefinitions.value.forEach((def) => {
    const instance = pxLocks.value.find(
      (lock) => lock.edge === props.selectedEdge.id && lock.definition === def.id,
    )
    if (instance) {
      state.value[def.id] = {
        defId: def.id,
        defName: getNameFromDefinitionId(def.id),
        currentCount: instance.count,
        newCount: instance.count,
        lockId: instance.id,
      }
    } else {
      state.value[def.id] = {
        defId: def.id,
        defName: getNameFromDefinitionId(def.id),
        currentCount: 0,
        newCount: 0,
        lockId: undefined,
      }
    }
  })

  //console.log(`successfully initialized state. found ${Object.entries(state.value).length} locks for edge with id ${props.selectedEdge.id}`)
  //console.log(`state: ${JSON.stringify(state.value)}`)
}

async function onSubmit() {
  Object.values(state.value).forEach(async (info) => {
    if (!info.lockId && info.newCount > 0) {
      // create new lock
      const lockId = await createPxLock({
        px_chart: props.chartId,
        edge: props.selectedEdge.id,
        definition: info.defId,
        count: info.newCount,
      })
      info.lockId = lockId
    } else if (info.lockId && info.currentCount > 0 && info.newCount === 0) {
      // delete existing lock
      await deletePxLock(info.lockId)
      info.lockId = undefined
    } else if (info.lockId && info.currentCount !== info.newCount) {
      // update existing lock
      await updatePxLock(info.lockId, {
        edge: props.selectedEdge.id,
        definition: info.defId,
        count: info.newCount,
      })
    }
    info.currentCount = info.newCount
  })

  emit('close', { edgeId: props.selectedEdge.id })
}
</script>

<template>
  <UModal :title="'Add/Edit Locks'">
    <template #body>
      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <div v-for="entry in Object.entries(state)" :key="entry[0]">
          <UFieldGroup>
            <UBadge
              class="min-w-64"
              :label="entry[1].defName"
              size="lg"
              :variant="entry[1].newCount ? 'subtle' : 'outline'"
              :color="entry[1].newCount ? 'primary' : 'neutral'"
            />
            <UInputNumber
              v-model="entry[1].newCount"
              variant="outline"
              :color="entry[1].newCount ? 'primary' : 'neutral'"
            />
          </UFieldGroup>
        </div>

        <UButton class="right-0" type="submit"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
