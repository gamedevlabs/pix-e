<script setup lang="ts">
import { computed } from 'vue'
import { useAuthentication } from '~/studyMock'

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
    class="border border-gray-100 dark:border-gray-800/60 bg-gray-50/60 dark:bg-gray-900/60"
    :class="{ 'opacity-55 pointer-events-none': isInactive }"
    :ui="{
      header: 'py-2.5 px-4',
      body: 'py-3 px-4',
    }"
  >
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2 min-w-0">
          <UIcon :name="icon" class="size-3.5 text-gray-400 dark:text-gray-500 shrink-0" />
          <h3
            class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide truncate"
          >
            {{ title }}
          </h3>
        </div>
        <slot name="actions" />
      </div>
    </template>

    <div v-if="isInactive" class="text-center py-5">
      <UIcon name="i-lucide-lock" class="text-gray-300 dark:text-gray-700 size-6 mb-1.5" />
      <p class="text-xs text-gray-400 dark:text-gray-500">Log in to access</p>
    </div>
    <slot v-else />
  </UCard>
</template>
