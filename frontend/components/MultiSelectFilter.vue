<template>
  <UDropdownMenu :items="dropdownItems" :ui="dropdownUi" class="w-full">
    <!-- Button showing current selections -->
    <UButton
      :label="buttonLabel"
      trailing-icon="i-heroicons-chevron-down-20-solid"
      class="w-full justify-between bg-input-background text-text border border-border hover:bg-hover-background focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 ease-in-out h-10"
    />

    <!-- Dropdown content: List of options with checkboxes -->
    <template #item="{ item }">
      <div class="block w-full px-2 py-1">
        <UCheckbox
          :model-value="item.checked"
          :label="item.label"
          class="block w-full text-[#00f5ff] hover:text-[#00ffff] transition-colors duration-200 font-mono"
          :ui="checkboxUi"
          @update:model-value="toggleOption(item.value)"
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
    default: () => [],
  },
  modelValue: {
    type: Array as () => string[],
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Select items',
  },
})

const emit = defineEmits(['update:modelValue'])

// Computed dropdown items: each option with label, value, checked
const dropdownItems = computed(() =>
  props.options.map((option) => ({
    label: option,
    value: option,
    checked: props.modelValue.includes(option),
  })),
)

// Toggle selection for option
const toggleOption = (optionValue: string) => {
  const isSelected = props.modelValue.includes(optionValue)
  const updatedSelection = isSelected
    ? props.modelValue.filter((item) => item !== optionValue)
    : [...props.modelValue, optionValue]
  emit('update:modelValue', updatedSelection)
}

// Button label text logic
const buttonLabel = computed(() => {
  const count = props.modelValue.length
  if (count === 0) return props.placeholder
  if (count === props.options.length) return 'All selected'
  return props.modelValue.join(', ')
})

// Neon-style theme for dropdown and checkboxes
const dropdownUi = {
  width: 'w-full',
  background: 'bg-[#0f0f23] text-[#00f5ff] border border-[#00f5ff] shadow-lg shadow-[#00f5ff]/30',
  ring: 'ring-2 ring-[#00f5ff]',
  item: {
    base: 'block w-full',
    disabled: 'cursor-not-allowed opacity-50',
  },
  content: 'flex flex-col gap-1 max-h-64 overflow-y-auto',
}

const checkboxUi = {
  label: 'text-[#00f5ff]',
  base: 'h-4 w-4 text-[#00f5ff] border border-[#00f5ff] rounded focus:ring-[#00f5ff]',
  background: 'bg-[#1a1a3d]',
  checked: 'bg-[#00f5ff] border-[#00f5ff]',
  indeterminate: 'bg-[#00f5ff] border-[#00f5ff]',
  disabled: 'cursor-not-allowed opacity-50',
}
</script>
