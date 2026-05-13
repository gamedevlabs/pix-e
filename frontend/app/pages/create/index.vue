<script setup lang="ts">
import CreateProgressStepper from '~/components/create-project/CreateProgressStepper.vue'
import CreateStepBasics from '~/components/create-project/CreateStepBasics.vue'
import CreateStepDetails from '~/components/create-project/CreateStepDetails.vue'
import CreateStepReview from '~/components/create-project/CreateStepReview.vue'
import IconUploadModal from '~/components/create-project/IconUploadModal.vue'
import OnboardingTrigger from '~/components/onboarding/OnboardingTrigger.vue'

definePageMeta({
  middleware: 'authentication',
})

const {
  form,
  errors,
  currentStep,
  steps,
  submitting,
  uploadedFile,
  previewUrl,
  isUploadModalOpen,
  canGoNext,
  isFirstStep,
  isLastStep,
  avatarText,
  nextStep,
  previousStep,
  goToStep,
  cancel,
  createNewProject,
} = useCreateProjectProcess()
</script>

<template>
  <div>
    <OnboardingTrigger mode="floating" />

    <UContainer class="py-10">
      <div class="max-w-3xl mx-auto">
        <div class="mb-8">
          <h1 class="text-3xl font-bold mb-2">Create New Project</h1>
          <p class="text-gray-600 dark:text-gray-400">
            Follow the steps below to set up your new game project
          </p>
        </div>

        <div class="mb-8">
          <CreateProgressStepper :current-step="currentStep" :steps="steps" />
        </div>

        <UCard class="mb-6">
          <div class="min-h-75">
            <CreateStepBasics
              v-if="currentStep === 1"
              v-model:name="form.name"
              v-model:short-description="form.shortDescription"
              :icon-url="form.icon"
              :preview-url="previewUrl"
              :avatar-text="avatarText"
              :submitting="submitting"
              @open-upload-modal="isUploadModalOpen = true"
            />

            <CreateStepDetails
              v-if="currentStep === 2"
              v-model:genre="form.genres"
              v-model:target-platform="form.targetPlatform"
              :submitting="submitting"
              :errors="errors"
            />

            <CreateStepReview
              v-if="currentStep === 3"
              :name="form.name"
              :short-description="form.shortDescription"
              :genre="form.genres"
              :target-platform="form.targetPlatform"
              :icon-url="form.icon"
              :preview-url="previewUrl"
              :avatar-text="avatarText"
              @edit-step="goToStep"
            />
          </div>
        </UCard>

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

    <IconUploadModal v-model:open="isUploadModalOpen" v-model:file="uploadedFile" />
  </div>
</template>
