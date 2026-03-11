<!-- frontend/app/components/player-expectations-new/dashboard/ApiErrorAlert.vue
What this component does:
takes an "error" value (could be anything).
  -> converts it into a readable string.
    -> If there is any text, shows a red alert box with the error message. -->
<script setup lang="ts">
import { computed, unref } from 'vue'
import { errorToText } from '~/utils/playerExpectationsNewDashboard'

const props = defineProps<{
  error: unknown
}>()

const text = computed(() => errorToText(unref(props.error)))
</script>

<template>
  <UAlert v-if="text" color="error" variant="soft" title="API error">
    <pre class="text-xs whitespace-pre-wrap">{{ text }}</pre>
  </UAlert>
</template>
