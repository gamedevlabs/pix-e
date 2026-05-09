<script setup lang="ts">
interface Props {
  /**
   * Tooltip text shown on hover.
   * Keep it short; this is primarily a dev-facing indicator.
   */
  title?: string
  /** Badge label text */
  label?: string
}

withDefaults(defineProps<Props>(), {
  title: 'Mock data (feature not wired up yet)',
  label: 'Mock',
})
</script>

<template>
  <UBadge color="neutral" variant="soft" size="xs" class="cursor-help" :title="title">
    {{ label }}
  </UBadge>
</template>
