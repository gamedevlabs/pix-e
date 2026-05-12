<script setup lang="ts">
const props = defineProps<{ chartId: string; settings: PxChartSettings }>()

const { updateItem: updateSettings } = usePxChartSettings(props.chartId)

const emit = defineEmits<{
  close: [newSettings: EditableSettings]
}>()

export type EditableSettings = Pick<
  PxChartSettings,
  'use_locks' | 'ignore_consumable_keys' | 'show_soft_locks'
>

const state: Ref<EditableSettings> = ref({
  use_locks: props.settings.use_locks,
  ignore_consumable_keys: props.settings.ignore_consumable_keys,
  show_soft_locks: props.settings.show_soft_locks,
})

const items = [
  /*
  {
    label: 'General',
    icon: 'i-lucide-settings',
    slot: 'general'
  },
  */
  {
    label: 'Paths',
    icon: 'i-lucide-waypoints',
    slot: 'pathfinding',
  },
]

async function onSubmit() {
  await updateSettings(props.settings.id, state.value)
  emit('close', state.value)
}
</script>

<template>
  <UModal :title="'PxChart Settings'" :close="{ onClick: () => emit('close', state) }">
    <template #body>
      <UTabs :items="items" class="gap-8 w-full">
        <template #pathfinding>
          <UForm :state="state" class="space-y-4" @submit="onSubmit">
            <h2>Pathfinding</h2>
            <USwitch
              v-model="state.use_locks"
              label="Use Locks & Keys"
              description="When enabled, path calculation will consider whether keys collected along a path can unlock all locks it contains."
            />

            <USeparator />
            <h2>Locks & Keys</h2>

            <UAlert
              v-if="!state.use_locks"
              color="neutral"
              variant="subtle"
              description="These settings only apply when locks & keys are enabled."
              icon="i-lucide-info"
            />

            <USwitch
              v-model="state.ignore_consumable_keys"
              label="Ignore Consumable Keys"
              description="When enabled, consumable keys will be treated as if they were reusable."
              :disabled="!state.use_locks"
            />
            <USwitch
              v-model="state.show_soft_locks"
              label="Show Soft Locks"
              description="When enabled, potential soft-locks will be highlighted."
              :disabled="!state.use_locks"
            />

            <UButton class="right-0 mt-6" type="submit"> Submit </UButton>
          </UForm>
        </template>
      </UTabs>
    </template>
  </UModal>
</template>

<style scoped></style>
