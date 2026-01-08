<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import type { Project, ProjectTargetPlatform } from '~/utils/project'
import { platformConfigs } from '~/utils/platformConfig'

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

async function createNewProject() {
  if (!validateStep(currentStep.value)) {
    return
  }

  submitting.value = true
  try {
    const created = await createProject({
      name: form.name!.trim(),
      shortDescription: form.shortDescription?.trim() ?? '',
      genre: form.genre.join(', '), // Join array into string
      targetPlatform: form.targetPlatform as Project['targetPlatform'],
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

// Genre suggestions
const genreSuggestions = [
  'Action',
  'Adventure',
  'RPG',
  'Strategy',
  'Simulation',
  'Puzzle',
  'Narrative',
  'Horror',
  'Platformer',
  'Sports',
]

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
            <div>
              <h2 class="text-xl font-semibold mb-4">Basic Information</h2>
              <p class="text-gray-600 dark:text-gray-400 mb-6">
                Let's start with the basics. What's the working title of your project?
              </p>
            </div>

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

            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 space-y-4">
              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400"
                  >Project Name</label
                >
                <p class="text-lg font-semibold mt-1">{{ form.name }}</p>
              </div>

              <div v-if="form.shortDescription">
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400"
                  >Description</label
                >
                <p class="mt-1">{{ form.shortDescription }}</p>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Genre</label>
                  <p class="font-medium mt-1">{{ form.genre.join(', ') }}</p>
                </div>
                <div>
                  <label class="text-sm font-medium text-gray-500 dark:text-gray-400"
                    >Platforms</label
                  >
                  <p class="font-medium mt-1 capitalize">
                    {{ form.targetPlatform.join(', ') }}
                  </p>
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
</template>

<style scoped>
/* Minimal scoped styles for transitions */
</style>
