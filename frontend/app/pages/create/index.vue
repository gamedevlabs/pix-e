<script setup lang="ts">
import { reactive, ref, computed, watch, onUnmounted } from 'vue'
import type { Project, ProjectTargetPlatform } from '~/utils/project.d'
import { genreSuggestions, platformConfigs, getPlatformConfig } from '~/utils/platformConfig'

const { createProject, switchProject } = useProjectHandler()
const router = useRouter()

definePageMeta({
  middleware: 'authentication',
})

// Wizard state
const currentStep = ref(1)
const totalSteps = 3
const submitting = ref(false)

// Form data
const form = reactive({
  name: '',
  shortDescription: '',
  genre: [] as string[], // Changed to array for multiple tags
  targetPlatform: [] as ProjectTargetPlatform[],
  // icon will be stored on the created project; local upload is kept separately
  icon: null as string | null,
})

// Uploaded file (not yet persisted) and preview URL
const uploadedFile = ref<File | null>(null)
const previewUrl = ref<string | null>(null)

// Avatar hover state and modal state
const isAvatarHovered = ref(false)
const isUploadModalOpen = ref(false)

watch(uploadedFile, (file, prev) => {
  // revoke previous object URL
  if (prev && previewUrl.value) {
    try {
      URL.revokeObjectURL(previewUrl.value)
    } catch {
      // Ignore revocation errors - this is expected when the URL is already revoked
    }
  }
  if (file) {
    previewUrl.value = URL.createObjectURL(file)
    // Close modal after successful upload
    isUploadModalOpen.value = false
  } else {
    previewUrl.value = null
  }
})

onUnmounted(() => {
  if (previewUrl.value) {
    try {
      URL.revokeObjectURL(previewUrl.value)
    } catch {
      // Ignore revocation errors - this is expected when the URL is already revoked
    }
  }
})

// Validation errors
const errors = reactive({
  name: '',
  shortDescription: '',
  genre: '',
  targetPlatform: '',
})

// Step definitions
const steps = [
  { number: 1, title: 'Basic Info', description: 'Name and description' },
  { number: 2, title: 'Project Details', description: 'Genre and platform' },
  { number: 3, title: 'Review', description: 'Confirm and create' },
]

// Computed
const canGoNext = computed(() => {
  if (currentStep.value === 1) {
    return form.name && form.name.trim().length > 0
  }
  if (currentStep.value === 2) {
    return form.genre.length > 0 && form.targetPlatform.length > 0
  }
  return true
})

const isLastStep = computed(() => currentStep.value === totalSteps)
const isFirstStep = computed(() => currentStep.value === 1)

// Avatar text (initials) or '?' when no name and no uploaded icon
const avatarText = computed(() => {
  // If there's an uploaded image or a saved icon URL, don't show text
  if (previewUrl.value || form.icon) return undefined
  const n = form.name?.trim()
  if (!n) return '?'
  const parts = n.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
})

// Methods
function validateStep(step: number): boolean {
  // Clear previous errors
  errors.name = ''
  errors.shortDescription = ''
  errors.genre = ''
  errors.targetPlatform = ''

  if (step === 1) {
    if (!form.name || form.name.trim().length === 0) {
      errors.name = 'Project name is required'
      return false
    }
    if (form.name.trim().length < 3) {
      errors.name = 'Project name must be at least 3 characters'
      return false
    }
  }

  if (step === 2) {
    if (form.genre.length === 0) {
      errors.genre = 'At least one genre is required'
      return false
    }
    if (form.targetPlatform.length === 0) {
      errors.targetPlatform = 'At least one target platform is required'
      return false
    }
  }

  return true
}

function nextStep() {
  if (!validateStep(currentStep.value)) {
    return
  }
  if (currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function cancel() {
  router.push('/')
}

function _removeUpload() {
  uploadedFile.value = null
}

function openUploadModal() {
  isUploadModalOpen.value = true
}

function closeUploadModal() {
  isUploadModalOpen.value = false
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      resolve(e.target?.result as string)
    }
    reader.onerror = (e) => reject(e)
    reader.readAsDataURL(file)
  })
}

async function createNewProject() {
  if (!validateStep(currentStep.value)) {
    return
  }

  submitting.value = true
  try {
    // If user uploaded a file, convert to data URL and attach as icon
    let iconToSend: string | null = null
    if (uploadedFile.value) {
      try {
        iconToSend = await fileToDataUrl(uploadedFile.value)
      } catch {
        // ignore conversion errors and continue without icon
        iconToSend = null
      }
    } else if (form.icon) {
      // user might have a preset icon URL (not in this flow), preserve it
      iconToSend = form.icon
    }

    const created = await createProject({
      name: form.name!.trim(),
      shortDescription: form.shortDescription?.trim() ?? '',
      genre: form.genre.join(', '), // Join array into string
      targetPlatform: form.targetPlatform as Project['targetPlatform'],
      icon: iconToSend,
    })

    // Show success message
    const toast = useToast()
    toast.add({
      title: 'Success!',
      description: `Project "${created.name}" has been created`,
      color: 'success',
      icon: 'i-heroicons-check-circle',
    })

    // Switch to the created project and navigate to dashboard
    await switchProject(created.id)
  } catch {
    const toast = useToast()
    toast.add({
      title: 'Error',
      description: 'Failed to create project. Please try again.',
      color: 'error',
      icon: 'i-heroicons-x-circle',
    })
    submitting.value = false
  }
}

function selectGenre(genre: string) {
  // Add genre to the array if it doesn't exist
  if (!form.genre.includes(genre)) {
    form.genre.push(genre)
  }
}

// Platform options now uses the shared configuration with icons
const platformOptions = platformConfigs
</script>

<template>
  <div>
    <UContainer class="py-10">
      <div class="max-w-3xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold mb-2">Create New Project</h1>
          <p class="text-gray-600 dark:text-gray-400">
            Follow the steps below to set up your new game project
          </p>
        </div>

        <!-- Progress Stepper -->
        <div class="mb-8">
          <div class="flex items-center justify-between">
            <div
              v-for="(step, index) in steps"
              :key="step.number"
              class="flex items-center"
              :class="{ 'flex-1': index < steps.length - 1 }"
            >
              <!-- Step Circle -->
              <div class="flex flex-col items-center">
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all"
                  :class="
                    currentStep >= step.number
                      ? 'bg-primary text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                  "
                >
                  <UIcon v-if="currentStep > step.number" name="i-heroicons-check" class="text-xl" />
                  <span v-else>{{ step.number }}</span>
                </div>
                <div class="mt-2 text-center">
                  <div
                    class="text-sm font-medium"
                    :class="
                      currentStep >= step.number ? 'text-gray-900 dark:text-white' : 'text-gray-500'
                    "
                  >
                    {{ step.title }}
                  </div>
                  <div class="text-xs text-gray-500">{{ step.description }}</div>
                </div>
              </div>

              <!-- Connector Line -->
              <div
                v-if="index < steps.length - 1"
                class="flex-1 h-0.5 mx-4 transition-all"
                :class="currentStep > step.number ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'"
              />
            </div>
          </div>
        </div>

        <!-- Step Content -->
        <UCard class="mb-6">
          <div class="min-h-[300px]">
            <!-- Step 1: Basic Info -->
            <div v-if="currentStep === 1" class="space-y-6">
              <!-- Title and description spanning full width -->
              <div>
                <h2 class="text-xl font-semibold mb-4">Basic Information</h2>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Let's start with the basics. What's the working title of your project?
                </p>
              </div>

              <!-- Two column layout -->
              <div class="grid grid-cols-2 gap-6">
                <!-- Left column: form inputs -->
                <div class="space-y-6">
                  <UFormField label="Project Name" required>
                    <UInput
                      v-model="form.name"
                      placeholder="My Awesome Game"
                      size="lg"
                      :disabled="submitting"
                    />
                  </UFormField>

                  <UFormField label="Short Description" optional>
                    <UTextarea
                      v-model="form.shortDescription"
                      placeholder="A brief description of your game project..."
                      :rows="2"
                      :disabled="submitting"
                    />
                  </UFormField>
                </div>

                <!-- Right column: avatar preview with hover effect -->
                <div class="flex flex-col items-center justify-center gap-4">
                  <div
                    class="relative cursor-pointer"
                    @mouseenter="isAvatarHovered = true"
                    @mouseleave="isAvatarHovered = false"
                    @click="openUploadModal"
                  >
                    <UAvatar
                      size="3xl"
                      :src="previewUrl || form.icon || undefined"
                      :text="avatarText"
                      class="transition-all duration-200"
                      :class="{ 'brightness-75': isAvatarHovered }"
                    />

                    <!-- Upload icon appears on hover - centered in circle -->
                    <div
                      v-if="isAvatarHovered"
                      class="absolute inset-0 flex items-center justify-center pointer-events-none"
                    >
                      <UIcon name="i-heroicons-arrow-up-tray" class="w-12 h-12 text-white" />
                    </div>
                  </div>

                  <div class="flex flex-col items-center gap-1">
                    <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Project Icon</p>
                    <p class="text-xs text-gray-500 text-center">You can upload your own icon</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 2: Project Details -->
            <div v-if="currentStep === 2" class="space-y-6">
              <div>
                <h2 class="text-xl font-semibold mb-4">Project Details</h2>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Tell us more about your project's genre and target platform
                </p>
              </div>

              <UFormField label="Genre" required>
                <UInputTags
                  v-model="form.genre"
                  :placeholder="form.genre.length === 0 ? 'e.g., Action, Adventure, RPG...' : ''"
                  size="lg"
                  :disabled="submitting"
                  icon="i-heroicons-tag"
                  :highlight="false"
                />
                <template #hint>
                  <p class="text-xs text-gray-500">Add one or more genres that describe your game.</p>
                </template>

                <div class="mt-2">
                  <div class="flex flex-wrap gap-2">
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
              </UFormField>

              <!-- Genre Suggestions -->

              <UFormField label="Target Platforms" required :error="errors.targetPlatform">
                <UCheckboxGroup
                  v-model="form.targetPlatform"
                  variant="table"
                  indicator="hidden"
                  :items="platformOptions"
                  :disabled="submitting"
                >
                  <template #label="{ item }">
                    <div class="flex items-center gap-2">
                      <UIcon :name="item.icon" class="w-5 h-5" />
                      <span>{{ item.label }}</span>
                    </div>
                  </template>
                </UCheckboxGroup>
                <template #hint>
                  <p class="text-xs text-gray-500 mt-2">
                    Select the platforms you intend to release your game on.
                  </p>
                </template>
              </UFormField>
            </div>

            <!-- Step 3: Review -->
            <div v-if="currentStep === 3" class="space-y-6">
              <div>
                <h2 class="text-xl font-semibold mb-4">Review Your Project</h2>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Almost done! Please review the information below before we create your project
                </p>
              </div>

              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 space-y-6">
                <!-- Project Icon and Name - Side by side -->
                <div
                  class="flex items-center gap-4 pb-4 border-b border-gray-200 dark:border-gray-700"
                >
                  <!-- Avatar with border/background -->
                  <div class="flex-shrink-0">
                    <div
                      class="p-2 bg-white dark:bg-gray-900 rounded-full ring-2 ring-gray-200 dark:ring-gray-700"
                    >
                      <UAvatar
                        size="xl"
                        :src="previewUrl || form.icon || undefined"
                        :text="avatarText"
                      />
                    </div>
                  </div>

                  <!-- Project Name -->
                  <div class="flex-1 group">
                    <div class="flex items-center gap-2 mb-1">
                      <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                        Project Name
                      </label>
                      <UButton
                        icon="i-heroicons-pencil"
                        color="neutral"
                        variant="ghost"
                        size="2xs"
                        class="opacity-0 group-hover:opacity-100 transition-opacity"
                        @click="currentStep = 1"
                      />
                    </div>
                    <p class="text-2xl font-bold">{{ form.name }}</p>
                  </div>
                </div>

                <!-- Short Description -->
                <div class="group">
                  <div class="flex items-center gap-2 mb-1">
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Description
                    </label>
                    <UButton
                      icon="i-heroicons-pencil"
                      color="neutral"
                      variant="ghost"
                      size="2xs"
                      class="opacity-0 group-hover:opacity-100 transition-opacity"
                      @click="currentStep = 1"
                    />
                  </div>
                  <p v-if="form.shortDescription" class="text-gray-700 dark:text-gray-300">
                    {{ form.shortDescription }}
                  </p>
                  <p v-else class="text-gray-400 dark:text-gray-500 italic">
                    No description provided
                  </p>
                </div>

                <div class="grid grid-cols-2 gap-6">
                  <!-- Genre -->
                  <div class="group">
                    <div class="flex items-center gap-2 mb-2">
                      <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                        Genre
                      </label>
                      <UButton
                        icon="i-heroicons-pencil"
                        color="neutral"
                        variant="ghost"
                        size="2xs"
                        class="opacity-0 group-hover:opacity-100 transition-opacity"
                        @click="currentStep = 2"
                      />
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <UBadge
                        v-for="genre in form.genre"
                        :key="genre"
                        :label="genre"
                        color="neutral"
                        variant="subtle"
                        size="md"
                      />
                    </div>
                  </div>

                  <!-- Platforms -->
                  <div class="group">
                    <div class="flex items-center gap-2 mb-2">
                      <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                        Platforms
                      </label>
                      <UButton
                        icon="i-heroicons-pencil"
                        color="neutral"
                        variant="ghost"
                        size="2xs"
                        class="opacity-0 group-hover:opacity-100 transition-opacity"
                        @click="currentStep = 2"
                      />
                    </div>
                    <div class="flex gap-3">
                      <UIcon
                        v-for="platform in form.targetPlatform"
                        :key="platform"
                        :name="getPlatformConfig(platform)?.icon || 'i-heroicons-square-3-stack-3d'"
                        class="w-8 h-8 text-gray-700 dark:text-gray-300"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <UAlert
                icon="i-heroicons-information-circle"
                color="info"
                variant="soft"
                title="What happens next?"
                description="After creating your project, you'll be automatically redirected to the project dashboard where you can start building your game."
              />
            </div>
          </div>
        </UCard>

        <!-- Navigation Buttons -->
        <div class="flex justify-between items-center">
          <UButton
            v-if="!isFirstStep"
            label="Back"
            color="neutral"
            variant="ghost"
            icon="i-heroicons-arrow-left"
            :disabled="submitting"
            @click="previousStep"
          />
          <UButton
            v-else
            label="Cancel"
            color="neutral"
            variant="ghost"
            :disabled="submitting"
            @click="cancel"
          />

          <div class="flex gap-3">
            <UButton
              v-if="!isLastStep"
              label="Next"
              color="primary"
              trailing-icon="i-heroicons-arrow-right"
              :disabled="!canGoNext || submitting"
              @click="nextStep"
            />
            <UButton
              v-else
              label="Create Project"
              color="primary"
              icon="i-heroicons-check"
              :loading="submitting"
              :disabled="submitting"
              @click="createNewProject"
            />
          </div>
        </div>
      </div>
    </UContainer>

    <!-- Upload Modal -->
    <div
      v-if="isUploadModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-25"
      @click="closeUploadModal"
    >
      <div
        class="bg-white dark:bg-gray-900 rounded-lg p-6 shadow-xl max-w-md w-full mx-4"
        @click.stop
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">Upload Project Icon</h3>
          <UButton
            icon="i-heroicons-x-mark"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="closeUploadModal"
          />
        </div>

        <UFileUpload
          v-model="uploadedFile"
          accept="image/*"
          icon="i-heroicons-photo"
          label="Drop your icon here"
          description="SVG, PNG, JPG or GIF (max. 2MB)"
          layout="grid"
          :interactive="false"
          class="w-full min-h-48"
        >
          <template #actions="{ open }">
            <UButton
              label="Select image"
              icon="i-heroicons-arrow-up-tray"
              color="neutral"
              variant="outline"
              @click="open()"
            />
          </template>
        </UFileUpload>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Minimal scoped styles for transitions */
</style>
