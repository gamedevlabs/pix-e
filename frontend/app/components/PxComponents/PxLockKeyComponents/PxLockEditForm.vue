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
const { items: pxKeyDefinitions, fetchAll: fetchPxKeyDefinitions } = usePxKeyDefinitions()

onMounted(() => {
  fetchPxLocks()
  fetchPxLockDefinitions()
  fetchPxKeyDefinitions()
  initialize()
})

export interface LockInfo {
  defId: string
  defName: string
  currentCount: number
  newCount: number
  lockId: string | undefined
  unlockedBy: string[]
}

const emit = defineEmits<{
  close: [edgeId: string]
}>()

function getNameFromDefinitionId(defId: string) {
  return pxLockDefinitions.value.find((def) => def.id === defId)!.name
}

function getNamesOfUnlockingKeys(lockDef: PxLockDefinition) {
  return lockDef.unlocked_by.map(
    (keyId) => pxKeyDefinitions.value.find((keyDef) => keyDef.id === keyId)!.name,
  )
}

const state: Ref<Record<string, LockInfo>> = ref({})

async function initialize() {
  await fetchPxLocks()
  await fetchPxKeyDefinitions()
  //console.log('initializing state...')

  let lockCount = 0
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
        unlockedBy: getNamesOfUnlockingKeys(def),
      }
      lockCount += instance.count
    } else {
      state.value[def.id] = {
        defId: def.id,
        defName: getNameFromDefinitionId(def.id),
        currentCount: 0,
        newCount: 0,
        lockId: undefined,
        unlockedBy: getNamesOfUnlockingKeys(def),
      }
    }
  })

  console.log(
    `successfully initialized state. found ${lockCount} locks for edge with id ${props.selectedEdge.id}`,
  )
  console.log(`initial state: ${JSON.stringify(state.value)}`)
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
      console.log(`Created new lock with id ${lockId}`)
    } else if (info.lockId && info.currentCount > 0 && info.newCount === 0) {
      // delete existing lock
      await deletePxLock(info.lockId)
      console.log(`Deleted lock with id ${info.lockId}`)
      info.lockId = undefined
    } else if (info.lockId && info.currentCount !== info.newCount) {
      // update existing lock
      await updatePxLock(info.lockId, {
        edge: props.selectedEdge.id,
        definition: info.defId,
        count: info.newCount,
      })
      console.log(`Updated lock with id ${info.lockId}`)
    }
    info.currentCount = info.newCount
  })

  emit('close', props.selectedEdge.id)
  console.log(`updated state: ${JSON.stringify(state.value)}`)
}

function getColor(lockInfo: LockInfo) {
  if (!lockInfo.newCount) return 'neutral'
  return 'primary'
}
</script>

<template>
  <UModal
    :title="'Edit Locks on Edge'"
    :close="{ onClick: () => emit('close', selectedEdge.id) }"
  >
    <template #body>
      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <UFormField v-for="[id, lockInfo] of Object.entries(state)" :key="id" :name="`state.${id}`">
          <UFieldGroup>
            <UBadge
              class="min-w-64"
              :label="lockInfo.defName"
              size="lg"
              :variant="lockInfo.newCount ? 'subtle' : 'outline'"
              :color="getColor(lockInfo)"
            />
            <UInputNumber
              v-model="lockInfo.newCount"
              name="count"
              :variant="lockInfo.newCount ? 'subtle' : 'outline'"
              :color="getColor(lockInfo)"
              :min="0"
            />
            <UTooltip :text="lockInfo.unlockedBy.toString()">
              <UBadge
                label="🔑"
                :color="getColor(lockInfo)"
                :variant="lockInfo.newCount ? 'subtle' : 'outline'"
              />
            </UTooltip>
          </UFieldGroup>
        </UFormField>

        <UButton class="right-0" type="submit"> Submit </UButton>
      </UForm>
    </template>
  </UModal>
</template>

<style scoped></style>
