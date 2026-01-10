<script setup lang="ts">
import { reactive, ref, computed, watch, onMounted } from 'vue'
import type { Project, ProjectTargetPlatform } from '~/utils/project.d'
import { genreSuggestions, platformConfigs } from '~/utils/platformConfig'

const { updateProject, fetchProjectById, syncProjectFromUrl, selectProject } = useProjectHandler()
const router = useRouter()
const route = useRoute()
const toast = useToast()

definePageMeta({
  middleware: 'authentication',
})

// Sync project from URL
syncProjectFromUrl()

// Get project ID from URL query parameter
const projectId = computed(() => route.query.id as string | undefined)

// Form state
const formData = reactive({
  name: '',
  shortDescription: '',
  genre: [] as string[], // Changed to array for tags
  targetPlatform: [] as ProjectTargetPlatform[], // Changed to array for checkboxes
  icon: null as string | null,
})

const isLoading = ref(false)
const isSaving = ref(false)
const originalProject = ref<Project | null>(null)
const isIconHovered = ref(false)

// Check if form has changes
const hasChanges = computed(() => {
  if (!originalProject.value) return false

  const originalGenres = originalProject.value.genre
    .split(',')
    .map((g) => g.trim())
    .filter(Boolean)
  const currentGenres = formData.genre
  const originalPlatforms = Array.isArray(originalProject.value.targetPlatform)
    ? originalProject.value.targetPlatform
    : [originalProject.value.targetPlatform]

  const nameChanged = formData.name !== originalProject.value.name
  const descChanged = formData.shortDescription !== originalProject.value.shortDescription
  const genresChanged =
    JSON.stringify([...currentGenres].sort()) !== JSON.stringify([...originalGenres].sort())
  const platformsChanged =
    JSON.stringify([...formData.targetPlatform].sort()) !==
    JSON.stringify([...originalPlatforms].sort())
  const iconChanged = formData.icon !== originalProject.value.icon

  return nameChanged || descChanged || genresChanged || platformsChanged || iconChanged
})

// Load project data
const loadProject = async () => {
  if (!projectId.value) {
    toast.add({
      title: 'No Project Selected',
      description: 'Please select a project to edit',
      color: 'error',
    })
    router.push('/')
    return
  }

  isLoading.value = true
  try {
    const project = await fetchProjectById(projectId.value)
    if (!project) {
      toast.add({
        title: 'Project Not Found',
        description: `Project ${projectId.value} does not exist`,
        color: 'error',
      })
      router.push('/')
      return
    }

    originalProject.value = project
    formData.name = project.name
    formData.shortDescription = project.shortDescription
    // Parse genre string into array
    formData.genre = project.genre
      .split(',')
      .map((g) => g.trim())
      .filter(Boolean)
    // Parse targetPlatform into array
    formData.targetPlatform = (
      Array.isArray(project.targetPlatform) ? project.targetPlatform : [project.targetPlatform]
    ) as ProjectTargetPlatform[]
    formData.icon = project.icon || null
  } catch {
    toast.add({
      title: 'Error Loading Project',
      description: 'Failed to load project data',
      color: 'error',
    })
    router.push('/')
  } finally {
    isLoading.value = false
  }
}

// Handle cancel
const handleCancel = () => {
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Are you sure you want to cancel?')
    if (!confirmed) return
  }
  router.push(`/dashboard?id=${projectId.value}`)
}

// Handle submit
const handleSubmit = async () => {
  if (!projectId.value) return

  isSaving.value = true
  try {
    const updatedProject = await updateProject(projectId.value, {
      name: formData.name,
      shortDescription: formData.shortDescription,
      genre: formData.genre.join(', '), // Join array into string
      targetPlatform: formData.targetPlatform,
      icon: formData.icon,
    })

    if (updatedProject) {
      originalProject.value = updatedProject
      // Update the current project in the composable to refresh the sidebar
      await selectProject(updatedProject)
      // Don't show toast here - updateProject already shows one
      // Stay on the settings page instead of routing to dashboard
    }
  } catch {
    toast.add({
      title: 'Error Saving Project',
      description: 'Failed to save project settings',
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}

// Handle icon upload
const handleIconChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      formData.icon = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

// Remove icon
const removeIcon = () => {
  formData.icon = null
}

// Select genre from suggestions
const selectGenre = (genre: string) => {
  if (!formData.genre.includes(genre)) {
    formData.genre.push(genre)
  }
}

// Load project on mount and when ID changes
onMounted(() => {
  loadProject()
})

watch(
  () => route.query.id,
  () => {
    loadProject()
  },
)
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center min-h-[400px]">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary" />
      </div>

      <!-- Settings Form -->
      <div v-else class="max-w-3xl mx-auto">
        <div class="mb-8">
          <h1 class="text-3xl font-bold mb-2">Project Settings</h1>
          <p class="text-gray-500 dark:text-gray-400">
            Configure your project settings and preferences
          </p>
        </div>

        <form class="space-y-6" @submit.prevent="handleSubmit">
          <!-- Basic Information -->
          <UCard>
            <template #header>
              <h2 class="text-xl font-semibold">Basic Information</h2>
            </template>

            <div class="space-y-6">
              <!-- Avatar and Change Icon Button -->
              <div
                class="flex flex-col items-center gap-4 pb-6 border-b border-gray-200 dark:border-gray-700"
              >
                <!-- Larger avatar with hover delete icon -->
                <div
                  class="relative"
                  @mouseenter="isIconHovered = true"
                  @mouseleave="isIconHovered = false"
                >
                  <UAvatar
                    v-if="formData.icon"
                    :src="formData.icon"
                    :alt="formData.name"
                    size="2xl"
                  />
                  <UAvatar
                    v-else
                    :alt="formData.name"
                    size="2xl"
                    :text="formData.name.substring(0, 2).toUpperCase()"
                  />

                  <!-- Delete icon overlay when hovering over custom icon -->
                  <div
                    v-if="formData.icon && isIconHovered"
                    class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full cursor-pointer transition-opacity"
                    @click="removeIcon"
                  >
                    <UIcon name="i-lucide-trash-2" class="text-white text-2xl" />
                  </div>
                </div>

                <!-- Change Icon button below avatar -->
                <label class="cursor-pointer">
                  <UButton
                    label="Change Icon"
                    icon="i-lucide-upload"
                    color="primary"
                    variant="outline"
                    as="span"
                  />
                  <input type="file" accept="image/*" class="hidden" @change="handleIconChange" />
                </label>
              </div>

              <!-- Project Name -->
              <div>
                <label class="block text-sm font-medium mb-2">
                  Project Name <span class="text-red-500">*</span>
                </label>
                <UInput
                  v-model="formData.name"
                  placeholder="Enter project name"
                  size="lg"
                  required
                />
              </div>

              <!-- Short Description -->
              <div>
                <label class="block text-sm font-medium mb-2"> Short Description </label>
                <UTextarea
                  v-model="formData.shortDescription"
                  placeholder="Brief description of your project"
                  :rows="3"
                  size="lg"
                />
              </div>
            </div>
          </UCard>

          <!-- Project Details -->
          <UCard>
            <template #header>
              <h2 class="text-xl font-semibold">Project Details</h2>
            </template>

            <div class="space-y-6">
              <!-- Genre with Tags -->
              <div>
                <label class="block text-sm font-medium mb-2">
                  Genre <span class="text-red-500">*</span>
                </label>
                <UInputTags
                  v-model="formData.genre"
                  :placeholder="
                    formData.genre.length === 0 ? 'e.g., Action, Adventure, RPG...' : ''
                  "
                  size="lg"
                  icon="i-heroicons-tag"
                  :highlight="false"
                />

                <!-- Genre Suggestions -->
                <div class="mt-2 flex flex-wrap gap-2">
                  <UButton
                    v-for="genre in genreSuggestions"
                    :key="genre"
                    size="xs"
                    color="neutral"
                    variant="soft"
                    :label="genre"
                    @click="selectGenre(genre)"
                  />
                </div>
              </div>

              <!-- Target Platform with Checkboxes -->
              <div>
                <label class="block text-sm font-medium mb-2">
                  Target Platform <span class="text-red-500">*</span>
                </label>
                <UCheckboxGroup
                  v-model="formData.targetPlatform"
                  variant="table"
                  indicator="hidden"
                  :items="platformConfigs"
                >
                  <template #label="{ item }">
                    <div class="flex items-center gap-2">
                      <UIcon :name="item.icon" class="w-5 h-5" />
                      <span>{{ item.label }}</span>
                    </div>
                  </template>
                </UCheckboxGroup>
              </div>
            </div>
          </UCard>

          <!-- Project Metadata (Read-only Collapsible) -->
          <UCollapsible v-if="originalProject" class="flex flex-col gap-2">
            <UButton
              class="group bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700"
              color="neutral"
              variant="ghost"
              block
              :ui="{
                trailingIcon:
                  'group-data-[state=open]:rotate-180 transition-transform duration-200',
              }"
            >
              <template #leading>
                <UIcon name="i-lucide-info" class="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </template>
              <span class="flex-1 text-left font-semibold text-gray-700 dark:text-gray-300">
                Project Metadata
              </span>
              <template #trailing>
                <UIcon
                  name="i-lucide-chevron-down"
                  class="w-5 h-5 text-gray-500 dark:text-gray-400"
                />
              </template>
            </UButton>

            <template #content>
              <div
                class="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div class="space-y-3">
                  <div
                    class="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700"
                  >
                    <span class="text-sm font-medium text-gray-600 dark:text-gray-400">
                      <UIcon name="i-lucide-hash" class="inline-block w-4 h-4 mr-1" />
                      Project ID
                    </span>
                    <span class="text-sm font-mono text-gray-500 dark:text-gray-500 select-all">
                      {{ originalProject['id'] }}
                    </span>
                  </div>
                  <div
                    class="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700"
                  >
                    <span class="text-sm font-medium text-gray-600 dark:text-gray-400">
                      <UIcon name="i-lucide-calendar-plus" class="inline-block w-4 h-4 mr-1" />
                      Created
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-500">
                      {{
                        originalProject['created_at']
                          ? new Date(originalProject['created_at']).toLocaleString()
                          : 'N/A'
                      }}
                    </span>
                  </div>
                  <div class="flex justify-between items-center py-2">
                    <span class="text-sm font-medium text-gray-600 dark:text-gray-400">
                      <UIcon name="i-lucide-calendar-clock" class="inline-block w-4 h-4 mr-1" />
                      Last Updated
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-500">
                      {{
                        originalProject['updated_at']
                          ? new Date(originalProject['updated_at']).toLocaleString()
                          : 'N/A'
                      }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </UCollapsible>

          <!-- Action Buttons -->
          <div v-if="hasChanges" class="flex justify-end gap-3 pt-4">
            <UButton
              label="Cancel"
              color="neutral"
              variant="outline"
              size="lg"
              :disabled="isSaving"
              @click="handleCancel"
            />
            <UButton
              label="Save Changes"
              icon="i-lucide-save"
              color="primary"
              size="lg"
              type="submit"
              :loading="isSaving"
              :disabled="isSaving"
            />
          </div>
        </form>
      </div>
    </SimpleContentWrapper>
  </div>
</template>

<style scoped>
/* Minimal scoped styles for transitions */
</style>
