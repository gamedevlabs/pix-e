<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  icon: string
  loginRequired?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loginRequired: false,
})

const authentication = useAuthentication()
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

const isInactive = computed(() => props.loginRequired && !isLoggedIn.value)
</script>

<template>
  <UCard
    class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800"
    :class="{ 'opacity-60': isInactive }"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <UIcon :name="icon" class="text-gray-600 dark:text-gray-400" />
          <h3 class="font-semibold text-gray-900 dark:text-gray-100">{{ title }}</h3>
        </div>
        <slot name="actions" />
      </div>
    </template>

    <div v-if="isInactive" class="text-center py-8">
      <UIcon name="i-lucide-lock" class="text-gray-400 dark:text-gray-500 text-4xl mb-3" />
      <p class="text-sm text-gray-600 dark:text-gray-400">Please log in to access this feature</p>
    </div>
    <slot v-else />
  </UCard>
</template>
