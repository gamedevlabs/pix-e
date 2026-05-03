<script setup lang="ts">
defineProps<{
  currentStep: number
  steps: { number: number; title: string; description: string }[]
}>()
</script>

<template>
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
</template>
