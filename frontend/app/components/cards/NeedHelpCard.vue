<template>
  <DashboardCard title="Need Help?" icon="i-lucide-help-circle">
    <div class="space-y-2">
      <UButton
        label="Wiki"
        icon="i-lucide-book-open"
        color="neutral"
        variant="soft"
        size="sm"
        block
        :to="MOCK_EXTERNAL_LINKS.wiki"
        target="_blank"
        rel="noopener noreferrer"
      />
      <UButton
        label="Discord"
        icon="i-lucide-message-circle"
        color="neutral"
        variant="soft"
        size="sm"
        block
        :to="MOCK_EXTERNAL_LINKS.discord"
        target="_blank"
        rel="noopener noreferrer"
      />
    </div>
  </DashboardCard>
</template>

<script setup lang="ts">
import { MOCK_EXTERNAL_LINKS } from '~/studyMock'
</script>
