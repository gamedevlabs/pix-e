<script setup lang="ts">
const emit = defineEmits<{
  (e: 'addNewNode' | 'addExistingNode'): void
}>()

async function handleAddExistingNodeFromToolbar() {
  emit('addExistingNode')
}
async function handleAddNewNodeFromToolbar() {
  emit('addNewNode')
}
</script>

<template>
  <!-- Toolbar -->
  <UDashboardToolbar>
    <left>
      <div class="flex items-center gap-3">
        <!-- General buttons like settings and undo -->
        <UTooltip text="Undo changes" :content="{ align: 'center', side: 'right' }">
          <UButton size="xl" color="primary">
            <Icon name="i-heroicons-arrow-uturn-left-16-solid" />
          </UButton>
        </UTooltip>
        <UTooltip text="Redo changes" :content="{ align: 'center', side: 'right' }">
          <UButton size="xl" color="primary">
            <Icon name="i-heroicons-arrow-uturn-right-16-solid" />
          </UButton>
        </UTooltip>
        <USeparator orientation="vertical" class="h-10" size="sm" />

        <UTooltip text="Toggle snap to grid" :content="{ align: 'center', side: 'right' }">
          <USwitch
            unchecked-icon="material-symbols:grid-3x3-off"
            checked-icon="material-symbols:grid-3x3"
            color="primary"
            size="xl"
          />
        </UTooltip>
        <USeparator orientation="vertical" class="h-10" size="sm" />

        <!-- Most frequently used buttons -->
        <UTooltip text="Create new Node" :content="{ align: 'center', side: 'right' }">
          <UButton size="sm" color="primary" @click="handleAddNewNodeFromToolbar()">
            <Icon name="i-heroicons-plus-solid" size="2em" />
            Create <br />
            new node
          </UButton>
        </UTooltip>
        <UTooltip text="Add existing Node" :content="{ align: 'center', side: 'right' }">
          <UButton size="sm" color="primary" @click="handleAddExistingNodeFromToolbar()">
            <Icon name="i-heroicons-arrow-up-on-square" size="2em" />
            Add <br />
            existing node
          </UButton>
        </UTooltip>
        <USeparator orientation="vertical" class="h-10" size="sm" />
      </div>
    </left>

    <right>
      <div class="flex items-center gap-3">
        <!-- Analysis buttons/menus, less frequently used -->
        Placeholder for Analysis menus
      </div>
    </right>
  </UDashboardToolbar>
</template>

<style scoped></style>
