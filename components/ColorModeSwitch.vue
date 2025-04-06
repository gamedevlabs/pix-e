<script setup lang="ts">
const colorMode = useColorMode()

function switchColorMode() {
  colorMode.preference = mode.value ? 'dark' : 'light'
}

const mode = ref(colorMode.value === 'dark')
</script>

<template>
  <USwitch
    v-model="mode"
    color="neutral"
    size="xl"
    default-value
    unchecked-icon="i-lucide-moon"
    checked-icon="i-lucide-sun"
    @update:model-value="switchColorMode"
  />
</template>

<style scoped></style>
