<template>
  <UDropdownMenu
    :items="dropdownItems"
    :ui="dropdownUi"
    class="w-full"
  >
    <!-- Button showing selections -->
    <UButton
      :label="buttonLabel"
      trailing-icon="i-heroicons-chevron-down-20-solid"
      class="w-full justify-between bg-input-background text-text border border-border hover:bg-hover-background focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 ease-in-out"
    />

    <!-- Force Vertical List of Options -->
    <template #item="{ item }">
      <div class="block w-full px-2 py-1">
        <UCheckbox
          :model-value="item.checked"
          :label="item.label"
          @update:model-value="toggleOption(item.value)"
          class="block w-full text-[#00f5ff] hover:text-[#00ffff] transition-colors duration-200 font-mono"
          :ui="checkboxUi"
        />
      </div>
    </template>
  </UDropdownMenu>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Array as () => string[],
    default: () => []
  },
  modelValue: {
    type: Array as () => string[],
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select items'
  }
})

const emit = defineEmits(['update:modelValue'])

// Dropdown items array
const dropdownItems = computed(() =>
  props.options.map(option => ({
    label: option,
    value: option,
    checked: props.modelValue.includes(option)
  }))
)

// Toggle checkbox selection
const toggleOption = (optionValue: string) => {
  const newSelection = props.modelValue.includes(optionValue)
    ? props.modelValue.filter(item => item !== optionValue)
    : [...props.modelValue, optionValue]
  emit('update:modelValue', newSelection)
}

// Button label text
const buttonLabel = computed(() => {
  const count = props.modelValue.length
  if (count === 0) return props.placeholder
  if (count === props.options.length) return 'All selected'
  return props.modelValue.join(', ')
})

// Neon Theme Styles
const dropdownUi = {
  width: 'w-full',
  background: 'bg-[#0f0f23] text-[#00f5ff] border border-[#00f5ff] shadow-lg shadow-[#00f5ff]/30',
  ring: 'ring-2 ring-[#00f5ff]',
  item: {
    base: 'block w-full', // FORCE VERTICAL STACK
    disabled: 'cursor-not-allowed opacity-50'
  },
  content: 'flex flex-col gap-1 max-h-64 overflow-y-auto' // Vertical stacking for menu content
}

const checkboxUi = {
  label: 'text-[#00f5ff]',
  base: 'h-4 w-4 text-[#00f5ff] border border-[#00f5ff] rounded focus:ring-[#00f5ff]',
  background: 'bg-[#1a1a3d]',
  checked: 'bg-[#00f5ff] border-[#00f5ff]',
  indeterminate: 'bg-[#00f5ff] border-[#00f5ff]',
  disabled: 'cursor-not-allowed opacity-50'
}
</script>
