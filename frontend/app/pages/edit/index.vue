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
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Settings',
    icon: 'i-lucide-settings',
    navGroup: 'main',
    navOrder: 6,
    showInNav: true,
  },
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
  <div class="max-w-screen-2xl mx-auto w-full px-2 py-8 space-y-8">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-100">
      <UIcon name="i-lucide-loader-2" class="animate-spin size-8 text-primary" />
    </div>

    <template v-else>
      <!-- ─── Page title ──────────────────────────────────────────────── -->
      <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100 px-1">Settings</h1>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6 items-start">
          <!-- ─── Left: Main fields ────────────────────────────────────── -->
          <div class="space-y-6">
            <!-- Basic Information -->
            <UCard
              class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
              :ui="{ body: 'p-0' }"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="h-5 w-1 rounded-full bg-primary" />
                  <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">
                    Basic Information
                  </h2>
                </div>
              </template>

              <div class="px-5 pb-5 space-y-5">
                <!-- Project Name -->
                <UFormField label="Project Name" required>
                  <UInput
                    v-model="formData.name"
                    placeholder="Enter project name"
                    size="md"
                    class="w-full"
                    required
                  />
                </UFormField>

                <!-- Short Description -->
                <UFormField label="Short Description">
                  <UTextarea
                    v-model="formData.shortDescription"
                    placeholder="Brief description of your project"
                    :rows="3"
                    size="md"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>

            <!-- Project Details -->
            <UCard
              class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
              :ui="{ body: 'p-0' }"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="h-5 w-1 rounded-full bg-secondary-500" />
                  <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">
                    Project Details
                  </h2>
                </div>
              </template>

              <div class="px-5 pb-5 space-y-5">
                <!-- Genre -->
                <UFormField label="Genre">
                  <div class="space-y-2 w-full">
                    <UInputTags
                      v-model="formData.genre"
                      :placeholder="
                        formData.genre.length === 0 ? 'e.g. Action, Adventure, RPG…' : ''
                      "
                      size="md"
                      icon="i-lucide-tag"
                      :highlight="false"
                      class="w-full"
                    />
                    <div class="flex flex-wrap gap-1.5">
                      <UButton
                        v-for="genre in genreSuggestions"
                        :key="genre"
                        size="xs"
                        color="neutral"
                        variant="soft"
                        :label="genre"
                        :disabled="formData.genre.includes(genre)"
                        @click="selectGenre(genre)"
                      />
                    </div>
                  </div>
                </UFormField>

                <!-- Target Platform -->
                <UFormField label="Target Platform">
                  <UCheckboxGroup
                    v-model="formData.targetPlatform"
                    variant="table"
                    indicator="hidden"
                    :items="platformConfigs"
                    class="w-full"
                  >
                    <template #label="{ item }">
                      <div class="flex items-center gap-2">
                        <UIcon :name="item.icon" class="size-4" />
                        <span>{{ item.label }}</span>
                      </div>
                    </template>
                  </UCheckboxGroup>
                </UFormField>
              </div>
            </UCard>
          </div>

          <!-- ─── Right: Icon + Metadata ──────────────────────────────── -->
          <div class="space-y-6">
            <!-- Project Icon -->
            <UCard
              class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
              :ui="{ body: 'p-0' }"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="h-5 w-1 rounded-full bg-primary" />
                  <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Project Icon</h2>
                </div>
              </template>

              <div class="px-5 pb-5 flex flex-col items-center gap-4">
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
                    class="ring-2 ring-primary-200 dark:ring-primary-800"
                  />
                  <UAvatar
                    v-else
                    :alt="formData.name"
                    size="2xl"
                    :text="formData.name.substring(0, 2).toUpperCase()"
                    class="ring-2 ring-primary-200 dark:ring-primary-800 text-primary bg-primary-100 dark:bg-primary-900/50 font-bold"
                  />
                  <div
                    v-if="formData.icon && isIconHovered"
                    class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full cursor-pointer"
                    @click="removeIcon"
                  >
                    <UIcon name="i-lucide-trash-2" class="text-white size-5" />
                  </div>
                </div>

                <div class="flex gap-2">
                  <label class="cursor-pointer">
                    <UButton
                      label="Upload"
                      icon="i-lucide-upload"
                      color="neutral"
                      variant="outline"
                      size="sm"
                      as="span"
                    />
                    <input type="file" accept="image/*" class="hidden" @change="handleIconChange" />
                  </label>
                  <UButton
                    v-if="formData.icon"
                    label="Remove"
                    icon="i-lucide-trash-2"
                    color="error"
                    variant="soft"
                    size="sm"
                    @click="removeIcon"
                  />
                </div>

                <p class="text-xs text-gray-400 dark:text-gray-500 text-center">
                  PNG, JPG or GIF — displayed as your project avatar
                </p>
              </div>
            </UCard>

            <!-- Metadata (read-only) -->
            <UCard
              v-if="originalProject"
              class="border border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-900/60"
              :ui="{ body: 'p-0' }"
            >
              <template #header>
                <div class="flex items-center gap-3">
                  <div class="h-5 w-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                  <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Metadata</h2>
                </div>
              </template>

              <div class="px-5 pb-4 space-y-3">
                <div class="flex items-center justify-between gap-2">
                  <div
                    class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0"
                  >
                    <UIcon name="i-lucide-hash" class="size-3.5" />
                    <span>ID</span>
                  </div>
                  <span
                    class="text-xs font-mono text-gray-400 dark:text-gray-500 truncate select-all"
                  >
                    {{ originalProject['id'] }}
                  </span>
                </div>
                <USeparator />
                <div class="flex items-center justify-between gap-2">
                  <div
                    class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0"
                  >
                    <UIcon name="i-lucide-calendar-plus" class="size-3.5" />
                    <span>Created</span>
                  </div>
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {{
                      originalProject['created_at']
                        ? new Date(originalProject['created_at']).toLocaleDateString()
                        : 'N/A'
                    }}
                  </span>
                </div>
                <USeparator />
                <div class="flex items-center justify-between gap-2">
                  <div
                    class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0"
                  >
                    <UIcon name="i-lucide-calendar-clock" class="size-3.5" />
                    <span>Updated</span>
                  </div>
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {{
                      originalProject['updated_at']
                        ? new Date(originalProject['updated_at']).toLocaleDateString()
                        : 'N/A'
                    }}
                  </span>
                </div>
              </div>
            </UCard>
          </div>
        </div>

        <!-- ─── Save bar ────────────────────────────────────────────────── -->
        <Transition name="slide-up">
          <div v-if="hasChanges" class="sticky bottom-4 z-10">
            <UCard
              class="border border-primary/30 bg-white/90 dark:bg-gray-900/90 backdrop-blur shadow-lg"
              :ui="{ body: 'px-5 py-3' }"
            >
              <div class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <UIcon name="i-lucide-circle-dot" class="size-3.5 text-primary animate-pulse" />
                  You have unsaved changes
                </div>
                <div class="flex gap-2">
                  <UButton
                    label="Discard"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    :disabled="isSaving"
                    @click="handleCancel"
                  />
                  <UButton
                    label="Save Changes"
                    icon="i-lucide-save"
                    color="primary"
                    size="sm"
                    type="submit"
                    :loading="isSaving"
                  />
                </div>
              </div>
            </UCard>
          </div>
        </Transition>
      </form>
    </template>
  </div>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
