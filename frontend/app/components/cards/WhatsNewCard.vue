<script setup lang="ts">
import { mockWhatsNew } from '~/studyMock'

interface Update {
  title: string
  description: string
  icon?: string
}

interface Props {
  mockUpdates?: Update[]
}

const props = defineProps<Props>()

// Use shared mock data by default (until wired to backend)
const mockUpdates = computed<Update[]>(
  () => props.mockUpdates ?? (mockWhatsNew as unknown as Update[]),
)
</script>

<template>
  <DashboardCard title="What's New" icon="i-lucide-sparkles">
    <template #actions>
      <MockDataBadge />
    </template>

    <div class="space-y-3 text-sm">
      <div v-for="(update, index) in mockUpdates" :key="index" class="flex gap-2">
        <UIcon :name="update.icon || 'i-lucide-circle-dot'" class="text-primary shrink-0 mt-0.5" />
        <div>
          <p class="font-medium text-gray-900 dark:text-gray-100">{{ update.title }}</p>
          <p class="text-xs text-gray-600 dark:text-gray-400">{{ update.description }}</p>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
