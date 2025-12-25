<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  project: Project | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const projectStore = useProject()

const form = reactive({
  name: '',
  include_concept: true,
  include_pillars: true,
  include_charts: true,
  include_nodes: true,
})

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) return
    const baseName = props.project?.name?.trim() || 'Untitled Project'
    form.name = `${baseName} (Copy)`
  },
)

function close() {
  isOpen.value = false
}

async function handleClone() {
  if (!props.project) return
  await projectStore.cloneProject(props.project.id, {
    name: form.name.trim() || 'Untitled Project (Copy)',
    include_concept: form.include_concept,
    include_pillars: form.include_pillars,
    include_charts: form.include_charts,
    include_nodes: form.include_nodes,
  })
  close()
}
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="text-lg font-semibold">Clone Project</div>
            <UButton
              icon="i-heroicons-x-mark"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="close"
            />
          </div>
        </template>

        <div class="space-y-4">
          <UInput v-model="form.name" placeholder="Project name" />

          <div class="space-y-2">
            <UCheckbox v-model="form.include_concept" label="Game concept" />
            <UCheckbox v-model="form.include_pillars" label="Pillars" />
            <UCheckbox v-model="form.include_charts" label="Charts" />
            <UCheckbox
              v-model="form.include_nodes"
              label="Nodes (includes component definitions)"
            />
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="ghost" label="Cancel" @click="close" />
            <UButton
              color="primary"
              :loading="projectStore.isCloning"
              label="Create clone"
              @click="handleClone"
            />
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
