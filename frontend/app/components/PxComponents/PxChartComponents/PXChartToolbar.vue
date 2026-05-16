<script setup lang="ts">
const emit = defineEmits<{
  (e: 'addNewNode'|'addExistingNode'): void
}>()

//TODO: Add container at 0,0 or current flow location, not total 0,0
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
      <div class="flex items-center gap-4">
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
      <div class="flex items-center gap-4">
        <USeparator orientation="vertical" class="h-10" size="sm" />
        Placeholder for Undo and Redo
        <USeparator orientation="vertical" class="h-10" size="sm" />
        Placeholder for Snap to grid toggle
      </div>
    </right>
  </UDashboardToolbar>
</template>

<style scoped></style>
