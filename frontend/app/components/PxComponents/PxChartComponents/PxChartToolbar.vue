<script setup lang="ts">
const emit = defineEmits<{
  (e: 'addNewNode' | 'addExistingNode' | 'toggleSnapToGrid' | 'editSettings'): void
}>()

const props = defineProps({
  menuSnapToGrid: Boolean,
})

const toolbarSnapToGrid = computed(() => props.menuSnapToGrid)

async function handleAddExistingNodeFromToolbar() {
  emit('addExistingNode')
}

async function handleAddNewNodeFromToolbar() {
  emit('addNewNode')
}

async function handleToggleSnapToGrid() {
  emit('toggleSnapToGrid')
}
</script>

<template>
  <!-- Toolbar -->
  <UDashboardToolbar>
    <div class="flex items-center gap-2">
      <!-- General buttons like settings and undo -->

      <UTooltip text="Undo changes" :content="{ align: 'center', side: 'right' }">
        <UButton
          size="xl"
          color="primary"
          icon="i-heroicons-arrow-uturn-left-16-solid"
          :disabled="true"
        />
      </UTooltip>
      <UTooltip text="Redo changes" :content="{ align: 'center', side: 'right' }">
        <UButton
          size="xl"
          color="primary"
          icon="i-heroicons-arrow-uturn-right-16-solid"
          :disabled="true"
        />
      </UTooltip>
      <USeparator orientation="vertical" class="h-10" size="sm" />

      <UTooltip text="Settings" :content="{ align: 'center', side: 'right' }">
        <UButton size="xl" icon="i-lucide-settings" color="primary" @click="emit('editSettings')" />
      </UTooltip>

      <UTooltip text="Toggle snap to grid (G)" :content="{ align: 'center', side: 'right' }">
        <USwitch
          v-model="toolbarSnapToGrid"
          unchecked-icon="material-symbols:grid-3x3-off"
          checked-icon="material-symbols:grid-3x3"
          color="primary"
          size="xl"
          @change="handleToggleSnapToGrid()"
        />
      </UTooltip>
      <USeparator orientation="vertical" class="h-10" size="sm" />

      <!-- Most frequently used buttons -->

      <UTooltip text="Create new Node (N)" :content="{ align: 'center', side: 'right' }">
        <UButton size="xs" color="primary" @click="handleAddNewNodeFromToolbar()">
          <Icon name="i-heroicons-plus-solid" size="2em" />
          Create <br />
          new node
        </UButton>
      </UTooltip>
      <UTooltip text="Add existing Node (M)" :content="{ align: 'center', side: 'right' }">
        <UButton size="xs" color="primary" @click="handleAddExistingNodeFromToolbar()">
          <Icon name="i-heroicons-arrow-up-on-square" size="2em" />
          Add <br />
          existing node
        </UButton>
      </UTooltip>
      <USeparator orientation="vertical" class="h-10" size="sm" />
    </div>

    <!-- Temporary Buttons -->
    <slot name="right" class="flex items-center gap-3">
      <!-- Analysis buttons/menus, less frequently used -->
      Placeholder for Analysis menus
    </slot>
  </UDashboardToolbar>
</template>

<style scoped></style>
