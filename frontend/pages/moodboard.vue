<template>
  <!-- Debug bar and forced alert removed -->
  <div class="moodboard-container">
    <div class="page-header">
      <h1>AI Moodboard</h1>
    </div>
    <div v-if="!sessionId">
      <div class="prompt-bar">
        <UButtonGroup>
          <UButton color="neutral" variant="subtle">
            <UIcon name="i-heroicons-cog-6-tooth-20-solid" class="mr-1 w-4 h-4" />
            Settings
          </UButton>
          <UDropdownMenu :items="dropdownItems">
            <UButton color="neutral" variant="outline" icon="i-heroicons-chevron-down-20-solid" />
            <template #item="{ item }">
              <div :class="['dropdown-item', { 'dropdown-item-selected': item.checked }]">
                <UIcon :name="item.icon || ''" class="mr-2 w-4 h-4" />
                <span>{{ item.label }}</span>
                <UIcon v-if="item.checked" name="i-heroicons-check-20-solid" class="dropdown-item-check ml-auto w-4 h-4" />
              </div>
            </template>
          </UDropdownMenu>
        </UButtonGroup>
        <UInput v-model="prompt" placeholder="Describe your gaming moodboard..." @keyup.enter="startSessionWithPrompt" class="prompt-input" />
        <!-- Color palette icon and popover -->
        <UPopover>
          <span
            class="palette-icon-btn"
            :style="{ background: colorPickerValue, border: '2px solid #e5e7eb' }"
            aria-label="Pick colors"
            tabindex="0"
          >
            <UIcon
              name="i-heroicons-swatch-20-solid"
              class="w-6 h-6"
              :style="{ color: getContrastColor(colorPickerValue) }"
            />
          </span>
          <template #content>
            <div class="palette-popover-panel">
              <UColorPicker v-model="colorPickerValue" class="p-2" />
              <UButton @click="addColorToPaletteFromPicker" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2">Add</UButton>
              <div class="palette-list mt-2">
                <span v-for="(color, idx) in colorPalette" :key="color" class="palette-color" :style="{ background: color }">
                  <span class="palette-remove" @click="removeColorFromPalette(idx)">&times;</span>
                </span>
              </div>
            </div>
          </template>
        </UPopover>
        <!-- Show palette chips inline for quick reference -->
        <div class="palette-inline-list">
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"></span>
        </div>
        <UButton @click="startSessionWithPrompt" :disabled="!prompt" class="ml-2">Start Moodboard</UButton>
      </div>
    </div>
    <div v-else>
      <!-- UAlert removed, toast will show loading instead -->
      <UDivider v-if="loading || images.length || moodboard.length" class="my-6" />
      <div v-if="images.length" class="section-card">
        <div class="section-header">
          <h2>Generated Images</h2>
        </div>
        <div class="images-list">
          <UCard v-for="img in images" :key="img.id" class="image-item">
            <img :src="getImageUrl(img.url)" :alt="img.prompt" />
            <template #footer>
              <UCheckbox :model-value="selectedImageIds.includes(img.id)" @update:model-value="(value) => onCheckboxChange(value === true, img.id)" :label="'Select'" />
            </template>
          </UCard>
        </div>
      </div>
      <div v-if="moodboard.length" class="section-card">
        <div class="section-header">
          <h2>Your Moodboard</h2>
        </div>
        <div class="images-list">
          <UCard v-for="img in moodboard" :key="img.id" class="image-item">
            <img :src="getImageUrl(img.url)" :alt="img.prompt" />
          </UCard>
        </div>
      </div>
      <div class="prompt-bar">
        <UButtonGroup>
          <UButton color="neutral" variant="subtle">
            <UIcon name="i-heroicons-cog-6-tooth-20-solid" class="mr-1 w-4 h-4" />
            Settings
          </UButton>
          <UDropdownMenu :items="dropdownItems">
            <UButton color="neutral" variant="outline" icon="i-heroicons-chevron-down-20-solid" />
            <template #item="{ item }">
              <div :class="['dropdown-item', { 'dropdown-item-selected': item.checked }]">
                <UIcon :name="item.icon || ''" class="mr-2 w-4 h-4" />
                <span>{{ item.label }}</span>
                <UIcon v-if="item.checked" name="i-heroicons-check-20-solid" class="dropdown-item-check ml-auto w-4 h-4" />
              </div>
            </template>
          </UDropdownMenu>
        </UButtonGroup>
        <UInput v-model="prompt" placeholder="Describe your gaming moodboard..." @keyup.enter="generateImages" class="prompt-input" />
        <!-- Color palette icon and popover -->
        <UPopover>
          <span
            class="palette-icon-btn"
            :style="{ background: colorPickerValue, border: '2px solid #e5e7eb' }"
            aria-label="Pick colors"
            tabindex="0"
          >
            <UIcon
              name="i-heroicons-swatch-20-solid"
              class="w-6 h-6"
              :style="{ color: getContrastColor(colorPickerValue) }"
            />
          </span>
          <template #content>
            <div class="palette-popover-panel">
              <UColorPicker v-model="colorPickerValue" class="p-2" />
              <UButton @click="addColorToPaletteFromPicker" :disabled="colorPalette.length >= maxPaletteColors || colorPalette.includes(colorPickerValue)" size="xs" class="ml-1 mt-2">Add</UButton>
              <div class="palette-list mt-2">
                <span v-for="(color, idx) in colorPalette" :key="color" class="palette-color" :style="{ background: color }">
                  <span class="palette-remove" @click="removeColorFromPalette(idx)">&times;</span>
                </span>
              </div>
            </div>
          </template>
        </UPopover>
        <!-- Show palette chips inline for quick reference -->
        <div class="palette-inline-list">
          <span v-for="color in colorPalette" :key="color" class="palette-inline-color" :style="{ background: color }"></span>
        </div>
        <UButton @click="generateImages" :disabled="loading || !prompt" class="ml-2">Generate Images</UButton>
        <UButton @click="endSession" color="error" class="ml-2 end-btn">End Moodboard</UButton>
      </div>
    </div>
    <div v-if="showFinalMoodboard && moodboard.length" class="section-card">
      <div class="section-header">
        <h2>Your Final Moodboard</h2>
      </div>
      <div class="images-list">
        <UCard v-for="img in moodboard" :key="img.id" class="image-item">
          <img :src="getImageUrl(img.url)" :alt="img.prompt" />
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, inject, nextTick } from 'vue'
import type { Ref } from 'vue'
import axios from 'axios'
import { useRuntimeConfig } from '#imports'
import type { DropdownMenuItem } from '@nuxt/ui'
import '@/assets/css/toast-loading-bar.css'

const sessionId = ref<string | null>(null)
const prompt = ref('')
const images = ref<any[]>([])
const moodboard = ref<any[]>([])
const selectedImageIds = ref<any[]>([])
const loading = inject('globalLoading') as Ref<boolean>
const showFinalMoodboard = ref(false)

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const dropdownMode = ref('default')

const dropdownItems = computed(() => [
  {
    label: 'Default',
    icon: 'i-heroicons-sparkles-20-solid',
    type: 'checkbox' as const,
    checked: dropdownMode.value === 'default',
    onUpdateChecked(checked: boolean) {
      if (checked) dropdownMode.value = 'default'
      else if (dropdownMode.value === 'default') dropdownMode.value = 'gaming'
    }
  },
  {
    label: 'Gaming',
    icon: 'i-heroicons-command-line-20-solid',
    type: 'checkbox' as const,
    checked: dropdownMode.value === 'gaming',
    onUpdateChecked(checked: boolean) {
      if (checked) dropdownMode.value = 'gaming'
      else if (dropdownMode.value === 'gaming') dropdownMode.value = 'default'
    }
  }
])

const colorPalette = ref<string[]>([])
const maxPaletteColors = 5
const colorPickerValue = ref('#00C16A')

const chip = computed(() => ({ backgroundColor: colorPickerValue.value }))

function addColorToPaletteFromPicker() {
  const color = colorPickerValue.value.trim()
  if (colorPalette.value.length < maxPaletteColors && !colorPalette.value.includes(color)) {
    colorPalette.value.push(color)
  }
}

function removeColorFromPalette(idx: number) {
  colorPalette.value.splice(idx, 1)
}

onMounted(() => {
  const saved = localStorage.getItem('moodboard-dropdown-mode')
  if (saved && (saved === 'default' || saved === 'gaming')) {
    dropdownMode.value = saved
  }
})

watch(dropdownMode, (val) => {
  localStorage.setItem('moodboard-dropdown-mode', val)
  if (val === 'gaming') {
    console.log('Gaming mode selected!')
  }
})

function onDropdownModeChange(val: string) {
  if (val === 'gaming') {
    console.log('Gaming mode selected!')
  }
}

function onCheckboxChange(checked: boolean, id: any) {
  if (checked) {
    if (!selectedImageIds.value.includes(id)) selectedImageIds.value.push(id)
  } else {
    selectedImageIds.value = selectedImageIds.value.filter((i: any) => i !== id)
  }
}

// Restore toast logic using Nuxt UI auto-imported useToast
const toast = useToast()

function showMoodboardToast() {
  toast.add({
    title: 'Generating Images...',
    description: 'Your AI moodboard is being created. This may take a few moments.',
    color: 'primary',
    class: 'moodboard-toast',
  })
}

function clearMoodboardToast() {
  toast.clear()
}

async function generateImages() {
  if (!sessionId.value || !prompt.value) return
  loading.value = true
  showMoodboardToast()
  // Compose prompt with palette
  let fullPrompt = prompt.value
  if (colorPalette.value.length) {
    fullPrompt += `, color palette: ${colorPalette.value.join(', ')}`
  }
  await axios.post(`${apiBase}/api/moodboard/generate/`, {
    session_id: sessionId.value,
    prompt: fullPrompt,
    selected_image_ids: selectedImageIds.value,
    mode: dropdownMode.value // <-- send mode to backend
  })
  await fetchMoodboard()
  loading.value = false
  clearMoodboardToast()
  prompt.value = ''
  selectedImageIds.value = []
}

async function startSessionWithPrompt() {
  if (!prompt.value) return
  const res = await axios.post(`${apiBase}/api/moodboard/start/`)
  sessionId.value = res.data.session_id
  await fetchMoodboard()
  await generateImages()
}

async function fetchMoodboard() {
  if (!sessionId.value) return
  const res = await axios.get(`${apiBase}/api/moodboard/${sessionId.value}/`)
  images.value = res.data.images.filter((img: any) => !img.is_selected)
  moodboard.value = res.data.moodboard || []
}

async function endSession() {
  if (!sessionId.value) return
  const res = await axios.post(`${apiBase}/api/moodboard/end/`, {
    session_id: sessionId.value,
    selected_image_ids: selectedImageIds.value
  })
  sessionId.value = null
  images.value = []
  moodboard.value = res.data.moodboard || []
  prompt.value = ''
  selectedImageIds.value = []
  showFinalMoodboard.value = true
}

// Utility: get contrast color (black or white) for icon visibility
function getContrastColor(hex: string) {
  // Remove # if present
  hex = hex.replace('#', '')
  if (hex.length === 3) {
    hex = hex.split('').map(x => x + x).join('')
  }
  const r = parseInt(hex.substr(0,2),16)
  const g = parseInt(hex.substr(2,2),16)
  const b = parseInt(hex.substr(4,2),16)
  // Perceived brightness
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 150 ? '#222' : '#fff'
}

const getImageUrl = (url: string) => {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return apiBase.replace(/\/$/, '') + url
}
</script>

<style scoped>
.moodboard-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  padding-bottom: 7rem;
}

:root {
  --moodboard-header-bg: var(--ui-color-primary-50, #f5f3ff);
  --moodboard-header-text: var(--ui-primary, #8b5cf6);
  --moodboard-section-bg: var(--ui-color-primary-50, #f5f3ff);
  --moodboard-section-text: var(--ui-primary, #8b5cf6);
}

html[data-theme="dark"], .dark {
  --moodboard-header-bg: linear-gradient(90deg, #2e1065 0%, #4c1d95 100%);
  --moodboard-header-text: #ede9fe;
  --moodboard-section-bg: #18181b;
  --moodboard-section-text: #a78bfa;
}

.page-header {
  background: var(--moodboard-header-bg);
  border-radius: 1.25rem;
  padding: 2.5rem 2rem 2rem 2rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.10);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  transition: background 0.3s, color 0.3s;
}

.page-header h1 {
  font-size: 2.8rem;
  font-weight: 900;
  color: var(--moodboard-header-text);
  margin: 0;
  letter-spacing: -1px;
  transition: color 0.3s;
}

.prompt-bar {
  position: fixed;
  left: 256px;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--prompt-bar-bg, #fff);
  padding: 1rem 2rem;
  box-shadow: 0 -2px 16px 0 rgba(0,0,0,0.08);
  border-top: 1px solid #e5e7eb;
  transition: background 0.3s, color 0.3s;
}

@media (max-width: 900px) {
  .prompt-bar {
    left: 0;
    right: 0;
    max-width: 100vw;
    padding: 1rem 0.5rem;
  }
}

.section-card {
  background: var(--moodboard-section-bg);
  border-radius: 1.25rem;
  padding: 2rem 2rem 2.5rem 2rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.08);
  transition: background 0.3s, color 0.3s;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.section-header h2 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--moodboard-section-text);
  margin: 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

/* Add dropdown checkmark styling */
:deep(.dropdown-item-check) {
  margin-left: auto;
  padding-left: 0.5rem;
  color: var(--ui-primary, #8b5cf6);
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item-selected {
  background: var(--ui-color-primary-50, #f5f3ff);
  color: var(--ui-primary, #8b5cf6);
}

html[data-theme="dark"] .dropdown-item-selected, .dark .dropdown-item-selected {
  background: var(--ui-color-primary-900, #4c1d95);
  color: var(--ui-color-primary-100, #ede9fe);
}

html[data-theme="dark"] .prompt-bar, .dark .prompt-bar {
  --prompt-bar-bg: #18181b;
  border-top: 1px solid #23272f;
}

.prompt-input {
  flex: 1;
  max-width: 600px;
  margin: 0 1rem;
}

.images-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}

.image-item {
  border: 1px solid #ccc;
  padding: 0.5rem;
  border-radius: 8px;
  background: var(--image-card-bg);
  width: 200px;
  text-align: center;
  transition: background 0.2s;
}

:root, html[data-theme="light"] {
  --image-card-bg: #fafafa;
}

html[data-theme="dark"], .dark {
  --image-card-bg: #23272f;
}

.end-btn {
  margin-left: 1rem;
}

.palette-picker {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  min-width: 220px;
  padding: 0.5rem 0.5rem 0.5rem 0;
}

.palette-list {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.palette-color {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-right: 0.15rem;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.08);
  cursor: pointer;
  transition: border 0.2s;
}

.palette-color:hover {
  border: 2px solid var(--ui-primary, #8b5cf6);
}

.palette-remove {
  position: absolute;
  top: -7px;
  right: -7px;
  background: #fff;
  color: #a1a1aa;
  border-radius: 50%;
  font-size: 0.9rem;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.10);
  cursor: pointer;
  border: 1px solid #e5e7eb;
  z-index: 2;
}

.palette-remove:hover {
  color: #ef4444;
  background: #fef2f2;
}

.palette-input {
  width: 120px;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  padding: 0.25rem 0.5rem;
  font-size: 1rem;
  outline: none;
  transition: border 0.2s;
}

.palette-input:disabled {
  background: #f3f4f6;
  color: #a1a1aa;
}

html[data-theme="dark"] .palette-color, .dark .palette-color {
  border: 2px solid #23272f;
  background: #23272f;
}

html[data-theme="dark"] .palette-remove, .dark .palette-remove {
  background: #18181b;
  color: #a1a1aa;
  border: 1px solid #23272f;
}

html[data-theme="dark"] .palette-remove:hover, .dark .palette-remove:hover {
  color: #ef4444;
  background: #2e1065;
}

html[data-theme="dark"] .palette-input, .dark .palette-input {
  background: #23272f;
  color: #ede9fe;
  border: 1px solid #23272f;
}

.palette-picker .ml-1 {
  margin-left: 0.5rem;
}

.palette-popover-panel {
  padding: 0.5rem 1rem 1rem 1rem;
  background: var(--moodboard-section-bg);
  border-radius: 1rem;
  box-shadow: 0 4px 24px 0 rgba(139,92,246,0.10);
}

.palette-inline-list {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  margin-left: 0.5rem;
}

.palette-inline-color {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #e5e7eb;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.08);
  margin-right: 0.1rem;
}

.palette-icon-btn {
  margin-left: 0.5rem;
  min-width: 36px;
  min-height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

html[data-theme="dark"] .palette-inline-color, .dark .palette-inline-color {
  border: 2px solid #23272f;
  background: #23272f;
}
</style>
<style>
.global-animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}

.animate-spin-toast .ui-toast-icon {
  animation: spin 1s linear infinite;
}
</style>